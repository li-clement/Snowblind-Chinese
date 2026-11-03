# -*- coding: utf-8 -*-
"""v18 —— 共享图集版中文字体（不需要改 XBE，靠 .lmp 里的“负偏移”让多个 .fnt 共用一张位图）

原理（全部来自 default.xbe 静态逆向 + xemu 实测）：
  0x7EF20  把整个 .lmp 一次 malloc + 一次 ReadFile 读进同一块内存 → 同容器内条目之间
           可以互相引用（都是同一 buffer 里的地址）。
  0x66890  .fnt 处理器：把  hdr+0x08(记录表) / +0x0C(kerning) / +0x10(位图头)
           三个字段 **就地加上本条目基址** 变成指针，再 tail-call 0xC9280。
           —— 它不校验大小、不校验正负，纯 32 位加法 ⇒ 允许“负偏移”。
  0xC9280  通用纹理创建：w=hb[0] h=hb[2]，取 pow2 建 A8 纹理，
           像素地址 = hb + hb[8] + 0x400（hb[8] 同样是加法，也可负）。
  ⇒ 主字体放一份完整图集；其余字体只留 1612B 的“薄头”（头+charmap+位图头），
    三个字段写成 (主条目偏移 - 自己偏移)，运行时正好指回主图集的像素/记录/kerning。
    每个字体仍有自己独立的位图头，所以 0xC9280 写 [hb+8]/[hb+0x14] 不会互相踩。

代价：纹理仍然是 N 张（无 patch 无法共用），但容器体积 ≈ 1/N。
用法: python3 build_v18.py --map gamefonta.fnt=14,gamefontmed.fnt=13,... [--dropjp] [--out x.iso]
"""
import argparse, os, struct, subprocess, sys
import glob

BASE = '/Users/lee/code/iso'
RES = os.path.join(BASE, "[XBOX].Baldur's.Gate.Dark.Alliance.[USA]", 'res')
BACK = os.path.join(BASE, 'backup_original')
ANA = os.path.join(BASE, 'analysis')
REC_START, ALIGN = 0x214, 0x80

_src = open(os.path.join(BASE, 'tools', 'build_v16b.py'), encoding='utf-8').read()
B = type(sys)('B')
exec(compile(_src[:_src.index('hanzi_set = open(')], 'build_v16b.py', 'exec'), B.__dict__)


def parse_lmp(b):
    c = struct.unpack_from('<I', b, 0)[0]
    out = []
    for i in range(c):
        p = 4 + i * 64
        out.append([b[p:p + 56].split(b'\x00', 1)[0].decode('latin1'),
                    *struct.unpack_from('<II', b, p + 56)])
    return out, c


def build_font_open(src_paths, px_h, hanzi_set, punct_set):
    """build_v16b.build_font 的无上限版，返回 (bytes, atw, ath, cnt, f)

    相对 v14~v16 的两处**必要修正**（都是实测 F12 画面查出来的）：
      (1) 拉丁/图标字形取 **多个原版字体的 code 并集**：`gamefontsmall` 比 bigfont 多一枚
          code 0x8C（0x80~0x86 是按键图标区），共享图集后若只用单一来源就会丢图标。
      (2) **重建 256×u16 charmap**（byte → 本字表中 code==byte 的下标，缺→0xFFFF）。
          v14~v16 直接照抄原版 charmap，但字表里跳过了 code 0x20(空格)，导致整体 off-by-one：
          0x20→'!'、0x21→'"'……凡走 8 位查表的文本（按键提示等）全部取后一个字。
          中文走 UTF-16 线性按 code 查找，所以正文一直没露馅。
      (3) 顺带把空格记录**保留**下来（空 rect + 原版 advance），否则 cmap[0x20]=0xFFFF
          会让 8 位路径在空格处直接查不到。
    """
    if isinstance(src_paths, str):
        src_paths = [src_paths]
    fonts = [B.load_font(p) for p in src_paths]
    f = fonts[0]
    entries, latinmap = [], {}
    for ff in fonts:
        for v in ff['recs']:
            c = v[0]
            if c in (0, 0xFFFF) or c in B.PUNCT_ORDS or c in latinmap:
                continue
            if c == 32:                       # 空格：无墨，但要占位并保留 advance
                entries.append((32, None))
                latinmap[32] = v
                continue
            g = B.extract_glyph_rows(ff, v)
            if g:
                entries.append((c, g))
                latinmap[c] = v
    latin_codes = set(latinmap)
    added = 0
    for ch in hanzi_set:
        if added >= B.NUM_HANZI:
            break
        if ord(ch) in latin_codes:
            continue
        g = B.render_em(ch, px_h, B.TTF)
        if g:
            entries.append((ord(ch), g))
            added += 1
    for ch in punct_set:
        if ord(ch) in latin_codes or any(e == ord(ch) for e, _ in entries):
            continue
        g = B.render_punct(ch, px_h, B.TTF)
        if g:
            entries.append((ord(ch), g))
    placed, atw, ath, atlas = B.pack_rows(entries, 1024)
    cnt = len(placed)
    recs = bytearray()
    for c, box in placed:
        o = latinmap.get(c)
        if box is None:                       # 空格等无墨字形：零尺寸 rect + 原版步进
            f5, adv, kern = (o[5], o[6], o[7]) if o else (6, 8, 0xFFFF)
            recs += struct.pack('<8H', c, 0, 0, 0, 0, f5, adv, kern)
            continue
        bx, by, w, h = box
        f5, adv, kern = (o[5], o[6], o[7]) if o else (6, w + 1, 0xFFFF)
        recs += struct.pack('<8H', c, bx, bx + w, by, by + h, f5, adv, kern)
    offSec = REC_START + cnt * 16
    offBmp = offSec + len(f['kerning'])
    # —— 重建 charmap（不能照抄原版，见 docstring (2)）
    rb = bytes(recs)
    code2idx = {}
    for i in range(cnt):
        code2idx.setdefault(struct.unpack_from('<H', rb, i * 16)[0], i)
    pre = b''.join(struct.pack('<H', code2idx.get(b, 0xFFFF)) for b in range(256))
    assert len(pre) == 0x200
    out = struct.pack('<HHIIII', cnt, 8, f['nsect'], REC_START, offSec, offBmp)
    out += pre + rb + f['kerning']
    out += struct.pack('<HH', atw, ath) + f['meta'] + atlas
    assert offBmp + 0x38 + 0x400 == len(out) - atw * ath
    return bytes(out), atw, ath, cnt, f


def thin_font(master_bytes, f, atw, ath, share_hb=False):
    """只有 头 + charmap + 位图头 的壳；三个字段留占位，装箱时再写真实负偏移

    ⚠️ nsect 必须写 **master 的** 而不是本字体原版的：段表(section table)是跟着 master 的
       kerning 区一起共享的，而 8 位绘制路径 0x668E0 会按 rec 的 f7 去遍历
       `[fnt+0x0C] + edx*2` 的段表。薄头若宣称自己的 nsect 和 master 不一致
       （原版 gamefontsmall=29 而 bigfont=28），这段遍历就会走飞 —— 表现正是
       「共享字体的 8 位文本画不出来」（主菜单底部 Ⓐ 提示整条消失）。
    """
    offBmp = REC_START                       # 位图头紧跟在 头+charmap 之后
    nsect = struct.unpack_from('<I', master_bytes, 4)[0]      # 段表跟着 master 走，nsect 必须取 master 的
    hdr = struct.pack('<HHIIII', struct.unpack_from('<H', master_bytes, 0)[0], 8,
                      nsect, REC_START, 0, offBmp)   # +8/+0xC 占位=0
    # 注意：这里刻意不校验 nsect == 本字体原版 nsect —— 原版 gamefontsmall=29、bigfont=28，
    # 薄头共享的是 master 的段表，用 29 会让 0x668E0 的段表遍历越界（未验证的假设，见笔记第二十一轮）
    pre = master_bytes[0x14:0x214]           # 用 master 重建后的 charmap，保持与共享字表一致
    if share_hb:
        # 省掉自带的 0x438 位图头副本，+0x10 直接指到 master 的位图头。
        # 依据（default.xbe 静态）：0xC9280 开头就是
        #     mov  eax,[ebp+0x14] / test eax,eax / jne 0xc9be2(ret)
        # 也就是**位图头级别已经有"已创建"缓存**：多个 .fnt 的 +0x10 指向同一个 hb 时，
        # 第一个字体建纹理并置 [hb+0x14]=-1、[hb+0x10]=资源指针，后面的字体直接 ret，
        # 既不会重复分配 pow2 纹理，也不会把 hb[8] 再加一次。
        # ⇒ 之前"共享只省容器不省纹理"的结论是错的：那是因为薄头各带一份 hb，哨兵各不相同。
        return hdr + pre                      # 0x214 字节
    meta = bytearray(f['meta'])
    meta[4:8] = struct.pack('<I', 0)         # 像素偏移占位（装箱时写负 delta）
    return hdr + pre + struct.pack('<HH', atw, ath) + bytes(meta)


def build_lmp(items):
    """items: [(name, bytes)] → 容器字节；同时返回每项最终偏移"""
    n = len(items)
    hdr_len = 4 + n * 64
    cur = hdr_len + (-hdr_len % ALIGN)
    offs = []
    for _, bb in items:
        offs.append(cur)
        cur += len(bb) + (-len(bb) % ALIGN)
    hdr = bytearray(struct.pack('<I', n))
    for (nm, bb), o in zip(items, offs):
        hdr += nm.encode('latin1')[:56].ljust(56, b'\x00') + struct.pack('<II', o, len(bb))
    body, pos = bytearray(), hdr_len
    for (nm, bb), o in zip(items, offs):
        body += b'\x00' * (o - pos) + bb
        pos = o + len(bb)
    return bytearray(hdr) + body, offs


def patch_thin(buf, thin_off, master_off, share_hb=False):
    """薄头三个字段 = “目标绝对偏移 - 自己基址”（32 位补码，可为负）。
       引擎 0x66890: fnt+0x08/+0x0C/+0x10 各自 += fnt_base；0xC9280: pix = hb + hb[8] + 0x400"""
    _, _, _, m_rec, m_sec, m_bmp = struct.unpack_from('<HHIIII', buf, master_off)
    t_rec, t_sec, t_bmp = struct.unpack_from('<III', buf, thin_off + 0x08)
    # 1) 记录表 → 主条目记录表
    struct.pack_into('<I', buf, thin_off + 0x08, (master_off + m_rec - thin_off) & 0xFFFFFFFF)
    # 2) kerning 段 → 主条目 kerning
    struct.pack_into('<I', buf, thin_off + 0x0C, (master_off + m_sec - thin_off) & 0xFFFFFFFF)
    # 3) 像素块：让 hb_t + hb[8] + 0x400 == 主条目像素起点
    if share_hb:
        # 位图头本体也共享：+0x10 指向 master 的 hb（引擎 [fnt+0x10] += fnt_base）
        struct.pack_into('<I', buf, thin_off + 0x10, (master_off + m_bmp - thin_off) & 0xFFFFFFFF)
        return
    hb_t = thin_off + t_bmp
    struct.pack_into('<I', buf, hb_t + 0x08,
                     (master_off + m_bmp + 0x38 - hb_t) & 0xFFFFFFFF)


def simulate(buf, ents):
    """按 0x66890 + 0xC9280 的算法模拟指针换算，检查是否全部落在容器内"""
    n = len(buf)
    rep = []
    for nm, off, size in ents:
        if not nm.endswith('.fnt'):
            continue
        cnt, hgt, nsect, recs, offSec, offBmp = struct.unpack_from('<HHIIII', buf, off)
        rp = (off + recs) & 0xFFFFFFFF
        kp = (off + offSec) & 0xFFFFFFFF
        hb = (off + offBmp) & 0xFFFFFFFF
        atw, ath, flag, doff = struct.unpack_from('<HHII', buf, hb)
        dp = (hb + doff + 0x400) & 0xFFFFFFFF
        ok = (0 <= rp and rp + cnt * 16 <= n and 0 <= dp and dp + atw * ath <= n
              and dp + atw * ath > hb)
        rep.append((nm, cnt, atw, ath, flag, dp - dp0[0] if dp0 else 0, dp, ok))
        sim_out.append((nm, dp, atw * ath, rp, cnt))
    return rep


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--map', default='gamefonta.fnt=14,gamefontmed.fnt=14,gamefontsmall.fnt=14,'
                                     'bigfont.fnt=14,creditfont.fnt=14')
    ap.add_argument('--dropjp', action='store_true', default=True)
    ap.add_argument('--keepjp', dest='dropjp', action='store_false')
    ap.add_argument('--out', default='')
    ap.add_argument('--charset', default='', help='字表文件，默认 translation/jobs/zh_charset.txt（并与译文用字取并集）')
    ap.add_argument('--dry', action='store_true')
    ap.add_argument('--sharehb', action='store_true',
                    help='薄头连位图头也共享（+0x10 指向 master 的 hb），纹理靠引擎自带的 '
                         '[hb+0x14] 缓存只建一份 —— 省的是真正的大头')
    ap.add_argument('--noshare', action='store_true', help='每个字体各自一张完整图集（对照组）')
    ap.add_argument('--thin', default='', help='只有这些字体做薄头(共享)，其余各自完整图集；空=全部可共享')
    a = ap.parse_args()
    pxof = dict((k.strip(), int(v)) for k, v in (kv.split('=') for kv in a.map.split(',')))
    # 字表来源：频率表只是起点，真正要保证的是「译文里出现的每个字都有字形」。
    # v14~v20 一直只用 zh_top1502.txt（频率表），实测译文用到 1687 个字而表里没有 463 个
    # （五、百、黄、红、绿、工、师、爱、热、跑、雷…），那些行会直接画成空白。
    # 守门必须在**任何写盘之前**：v21 那次试跑只 --map 了一个字体，先写了 .lmp 再退出，
    # 把树里其余 5 个字体打回原版（CJK 记录=0），排查时误以为构建器坏了。
    # 回封前守住门：工作备份留在游戏树里会被 extract-xiso 一起打包。
    # v21 第一次回封就把 19 个 .punctbak 打了进去（467 文件/2.79GB → 486 文件/2.92GB）。
    tree = os.path.dirname(RES)
    junk = [os.path.join(r, fn) for r, _, fs in os.walk(tree) for fn in fs
            if fn.endswith(('.bak', '.punctbak', '.tmp')) or fn == '.DS_Store']
    if junk:
        sys.exit(f'!! 游戏树里有 {len(junk)} 个工作备份/垃圾文件，先移走再回封：\n   '
                 + '\n   '.join(junk[:6]))

    hanzi = open(os.path.join(BASE, 'translation', 'jobs', 'zh_charset.txt'), encoding='utf-8').read()
    if a.charset:
        hanzi = open(a.charset, encoding='utf-8').read()
    import json as _json, re as _re
    used = set()
    for jp in glob.glob(os.path.join(BASE, 'translation', 'zh_*.uni.json')):
        for v in _json.load(open(jp, encoding='utf-8-sig')).values():
            used |= {c for c in str(v) if _re.match(r'[\u3000-\u303f\u4e00-\u9fff\uff00-\uffef\u2000-\u206f]', c)}
    extra = sorted(used - set(hanzi))
    hanzi += ''.join(extra)
    B.NUM_HANZI = len(hanzi)          # 关键：别让 NUM_HANZI 上限把补进来的字截掉
    print(f'  字表：charset {len(set(hanzi))} 字（译文用字 {len(used)}，本表新增覆盖 {len(extra)}）')
    punct = open(os.path.join(BASE, 'translation', 'jobs', 'zh_punct.txt'), encoding='utf-8').read()

    orig_font = open(os.path.join(BACK, 'font.lmp'), 'rb').read()
    fents = parse_lmp(orig_font)[0]
    orig_fe = open(os.path.join(BACK, 'frontend.lmp'), 'rb').read()
    fe_ents = parse_lmp(orig_fe)[0]
    srcs = {}
    for nm, off, size in fents + fe_ents:
        srcs.setdefault(nm, (orig_font if (off, size) in [(o, s) for _, o, s in fents] else orig_fe)[off:off + size])
    srcs = {}
    for nm, off, size in fents:
        srcs[nm] = orig_font[off:off + size]
    for nm, off, size in fe_ents:
        srcs.setdefault(nm, orig_fe[off:off + size])

    masters = {}   # (container, px) -> (bytes, atw, ath, cnt, f)
    thin_set = set(x.strip() for x in a.thin.split(',') if x.strip())
    def is_thin(nm):
        return (not a.noshare) and (nm in thin_set if thin_set else True)
    grp_taken, decisions = set(), {}

    def group_key(cont, nm, px):
        dk = (cont, nm, px)
        if dk in decisions:
            return decisions[dk]
        decisions[dk] = _group_key(cont, nm, px)
        return decisions[dk]

    def _group_key(cont, nm, px):
        """组键规则：同容器同 px 里 **第一个完整字体** 占据 (cont,px) 当 master，
           其后的完整字体各占 (cont,px,nm)；薄头一律指向 (cont,px)。"""
        g = (cont, px)
        if is_thin(nm):
            return g
        if g not in grp_taken:
            grp_taken.add(g)
            return g
        return (cont, px, nm)
    def get_master(cont, nm, px):
        key = group_key(cont, nm, px)
        if key not in masters and is_thin(nm):
            sys.exit(f'!! {cont}/{nm} 想做薄头，但同容器内 px={px} 还没有完整字体当 master')
        if key not in masters:
            print(f'  渲染 master [{cont}] {nm} px={px} ...')
            order = [nm] + [x for x in ('gamefonta.fnt', 'gamefontmed.fnt', 'gamefontsmall.fnt',
                                        'bigfont.fnt', 'creditfont.fnt') if x in srcs and x != nm]
            paths = []
            for x in order:
                sp = os.path.join(ANA, f'v18_src_{x}')
                open(sp, 'wb').write(srcs[x])
                paths.append(sp)
            masters[key] = build_font_open(paths, px, hanzi, punct)
            b, atw, ath, cnt, _ = masters[key]
            p2 = (1 << (atw - 1).bit_length(), 1 << (ath - 1).bit_length())
            print(f'    atlas {atw}x{ath} pow2={p2[0]}x{p2[1]} tex={p2[0]*p2[1]>>10}KB file={len(b)}B')
        return masters[key]

    global sim_out, dp0
    report = {}
    for cont, ents, orig in (('font.lmp', fents, orig_font), ('frontend.lmp', fe_ents, orig_fe)):
        items, role = [], []          # role: 'master'/'thin'/'orig'
        first = {}
        for nm, off, size in ents:
            if a.dropjp and nm.startswith('japfont'):
                role.append(('drop', None)); continue
            if nm in pxof:
                px = pxof[nm]
                key = group_key(cont, nm, px)
                if key not in masters:
                    get_master(cont, nm, px)
                mb = masters[key][0]
                if key in first and is_thin(nm):
                    role.append(('thin', key)); items.append((nm, b''))   # 占位，稍后填
                else:
                    first[key] = len(items); role.append(('master', key)); items.append((nm, mb))
            else:
                role.append(('orig', None)); items.append((nm, srcs[nm]))
        # 填薄头
        thinidx = []
        for i, (kind, key) in enumerate(role):
            if kind == 'thin':
                mb, atw, ath, cnt, f = masters[key]
                items[i] = (items[i][0], thin_font(mb, f, atw, ath, a.sharehb))
                thinidx.append((i, first[key]))
        buf, offs = build_lmp(items)
        # master 的绝对偏移 → 打薄头补丁
        for i, mi in thinidx:
            patch_thin(buf, offs[i], offs[mi], a.sharehb)
        # 校验
        ents2, _ = parse_lmp(bytes(buf))
        bad = []
        mdataptr = {}
        for nm, off, size in ents2:
            if not nm.endswith('.fnt'):
                continue
            cnt, hgt, nsect, recs, offSec, offBmp = struct.unpack_from('<HHIIII', buf, off)
            rp, kp, hb = (off + recs) & 0xFFFFFFFF, (off + offSec) & 0xFFFFFFFF, (off + offBmp) & 0xFFFFFFFF
            atw, ath, flag, doff = struct.unpack_from('<HHII', buf, hb)
            dp = (hb + doff + 0x400) & 0xFFFFFFFF
            ok = rp + cnt * 16 <= len(buf) and dp + atw * ath <= len(buf) and dp >= 0
            if not ok:
                bad.append(nm)
            mdataptr[nm] = (dp, atw, ath, rp, cnt, hb)
        shared = [k for k, v in role if k == 'thin']
        mkey = {i: key for i, (k, key) in enumerate(role)}
        ref = {}
        for i, (k, key) in enumerate(role):
            if k == 'master':
                nm0 = items[i][0]
                ref[key] = mdataptr[nm0][:2] + (mdataptr[nm0][3],)
        for i, (k, key) in enumerate(role):
            if k == 'thin':
                nm0 = items[i][0]
                want = ref[key]
                got = mdataptr[nm0][:2] + (mdataptr[nm0][3],)
                if got != want:
                    bad.append(f'{nm0} 共享指针不匹配 got={got} want={want}')
        # 纹理按 **唯一位图头** 计（0xC9280 的 [hb+0x14] 缓存），不是按 .fnt 条目数
        tex = 0
        uniq = {}
        for nm, (dp, atw, ath, rp, cnt, hb) in mdataptr.items():
            uniq.setdefault(hb, (atw, ath))
        for hb, (atw, ath) in uniq.items():
            tex += (1 << (atw - 1).bit_length()) * (1 << (ath - 1).bit_length())
        print(f'  {cont}: {len(orig)} -> {len(buf)}  .fnt 条目={len(mdataptr)} 纹理合计={tex/1048576:.2f}MB 校验={"OK" if not bad else "FAIL " + str(bad)}')
        for nm, (dp, atw, ath, rp, cnt, hb) in mdataptr.items():
            tag = '' if list(uniq).index(hb) == list(uniq).index(hb) else ''
            first_of = [n for n, v in mdataptr.items() if v[5] == hb][0]
            print(f'      {nm:20s} cnt={cnt:5d} atlas={atw}x{ath} pixptr=+{dp:07X} recptr=+{rp:07X} '
                  + ('纹理=自有' if first_of == nm else f'纹理=共用←{first_of}'))
        report[cont] = (bytes(buf), tex)
        open(os.path.join(ANA, f'v18_{cont}'), 'wb').write(buf)

    tot_tex = sum(v[1] for v in report.values())
    tot_c = sum(len(v[0]) for v in report.values())
    print(f'== 合计: 容器 {tot_c/1048576:.2f}MB  字体纹理 {tot_tex/1048576:.2f}MB')
    if a.dry:
        print('DRY'); return
    open(os.path.join(RES, 'font.lmp'), 'wb').write(report['font.lmp'][0])
    open(os.path.join(RES, 'frontend.lmp'), 'wb').write(report['frontend.lmp'][0])
    out = a.out or 'bgda_zh_v18.iso'
    p = os.path.join(BASE, out)
    if os.path.exists(p):
        os.remove(p)
    r = subprocess.run([os.path.join(BASE, 'extract-xiso-master', 'extract-xiso'), '-c',
                        os.path.basename(os.path.join(BASE, "[XBOX].Baldur's.Gate.Dark.Alliance.[USA]")), out],
                       cwd=BASE, capture_output=True, text=True)
    print(r.stdout[-300:], r.stderr[-300:], 'iso', os.path.getsize(p))


sim_out, dp0 = [], [0]
main()
