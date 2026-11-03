# -*- coding: utf-8 -*-
"""v17 —— “破限”验证/大字版生成器（基于 build_v16b.py，去掉 0x40000 自我限制）

静态逆向结论（default.xbe）：
  .lmp 容器:   0x7EF20  malloc((size+0x7FF)&~0x7FF + 0x100) + 一次 ReadFile  (整包读入)
  条目派发:    0x7EBxx  按扩展名派发  .tex->0xC9280  .fnt->0x66890  .uni->0xC6C20 ...
  .fnt 加载:   0x66890  把头 +8/+0xC/+0x10 三个偏移就地转成指针, 然后
                        jmp/tail-call 0xC9280(通用纹理创建), 传入 fnt+offBmp 作为“纹理头”
  纹理创建:    0xC9280  w=hdr[0] h=hdr[2] → pow2(w)×pow2(h), A8(fmt 0xB),
                        像素源 = hdr+0x38+0x400 = hdr+1080, 源pitch=w
  ⇒ .fnt 路径里没有任何 0x40000 常量/比较闸门；真正的硬约束是
     (a) pow2 取整后的纹理面积, (b) 容器整包 malloc 的内存预算。

用法:
  python3 build_v17.py [--px 13] [--pad 0] [--padrecs 0] [--dropjp] [--out NAME.iso]
                       [--nofe] [--dry]
"""
import argparse, os, shutil, struct, subprocess, sys

BASE = '/Users/lee/code/iso'
sys.path.insert(0, os.path.join(BASE, 'tools'))
RES = os.path.join(BASE, "[XBOX].Baldur's.Gate.Dark.Alliance.[USA]", 'res')
BACK = os.path.join(BASE, 'backup_original')
ANA = os.path.join(BASE, 'analysis')
REC_START = 0x214
ALIGN = 0x80

# 只借用 build_v16b.py 的“函数定义”部分（其顶层有构建代码，不能直接 import）
_src = open(os.path.join(BASE, 'tools', 'build_v16b.py'), encoding='utf-8').read()
_cut = _src.index('hanzi_set = open(')
B = type(sys)('B')
B.__dict__['__file__'] = 'build_v16b.py'
exec(compile(_src[:_cut], 'build_v16b.py', 'exec'), B.__dict__)


def build_font_open(src, dst, px_h, hanzi_set, punct_set, pad_bytes=0, pad_recs=0):
    """build_v16b.build_font 的无上限版：去掉 <0x40000 与 pow2<=256 断言。"""
    f = B.load_font(src)
    entries, latinmap = [], {}
    for v in f['recs']:
        c = v[0]
        if c in (0, 0xFFFF, 32) or c in B.PUNCT_ORDS:
            continue
        g = B.extract_glyph_rows(f, v)
        if g is None:
            continue
        entries.append((c, g))
        latinmap[c] = v
    latin_codes = set(latinmap) | {32}
    added = 0
    for ch in hanzi_set:
        if added >= B.NUM_HANZI:
            break
        c = ord(ch)
        if c in latin_codes:
            continue
        g = B.render_em(ch, px_h, B.TTF)
        if g:
            entries.append((c, g))
            added += 1
    for ch in punct_set:
        c = ord(ch)
        if c in latin_codes or any(ec == c for ec, _ in entries):
            continue
        g = B.render_punct(ch, px_h, B.TTF)
        if g:
            entries.append((c, g))

    placed, atw, ath, atlas = B.pack_rows(entries, 1024)
    p2 = (1 << (atw - 1).bit_length(), 1 << (ath - 1).bit_length())
    cnt = len(placed)
    recs = bytearray()
    for c, box in placed:
        if box is None:
            recs += struct.pack('<8H', c, 0, 0, 0, 0, 0, 8, 0xFFFF)
            continue
        bx, by, w, h = box
        if c in latinmap:
            o = latinmap[c]
            f5, adv, kern = o[5], o[6], o[7]
        else:
            f5, adv, kern = 6, w + 1, 0xFFFF
        recs += struct.pack('<8H', c, bx, bx + w, by, by + h, f5, adv, kern)

    # 可选：追加“够不着”的记录（code=0xFFFF）以在 *不改变纹理尺寸* 的前提下撑大文件
    for _ in range(pad_recs):
        recs += struct.pack('<8H', 0xFFFF, 0, 0, 0, 0, 0, 8, 0xFFFF)
    total_cnt = cnt + pad_recs

    offSec = REC_START + total_cnt * 16
    offBmp = offSec + len(f['kerning'])
    header = struct.pack('<HHIIII', total_cnt, 8, f['nsect'], f['magic'], offSec, offBmp)
    out = header + f['pre'] + bytes(recs) + f['kerning']
    out += struct.pack('<HH', atw, ath) + f['meta'] + atlas
    if pad_bytes:
        out += b'\x00' * pad_bytes          # 纯尾部填充：引擎完全不读，只测试“文件>0x40000”是否被拒
    open(dst, 'wb').write(out)
    eng_bm = offBmp + 0x38 + 0x400
    act_bm = len(out) - atw * ath - pad_bytes
    over = 'OVER0x40000' if len(out) >= 0x40000 else ''
    print(f'  {os.path.basename(dst):26s} px={px_h:2d} glyphs={cnt:5d}(+{pad_recs}rec) '
          f'atlas={atw}x{ath} pow2={p2[0]}x{p2[1]} tex={p2[0]*p2[1]>>10}KB '
          f'file={len(out):7d}B bm_match={eng_bm == act_bm} {over}')
    assert eng_bm == act_bm, '引擎像素起点与实际位图不符'
    return len(out), p2[0] * p2[1]


def parse_lmp(b):
    c = struct.unpack_from('<I', b, 0)[0]
    out = []
    for i in range(c):
        p = 4 + i * 64
        nm = b[p:p + 56].split(b'\x00', 1)[0].decode('latin1')
        off, size = struct.unpack_from('<II', b, p + 56)
        out.append([nm, off, size])
    return out, c


def build_lmp(names, blobs):
    n = len(names)
    hdr_len = 4 + n * 64
    cur = hdr_len + (-hdr_len % ALIGN)
    offs, cur2 = [], cur
    for bb in blobs:
        offs.append(cur2)
        cur2 += len(bb) + (-len(bb) % ALIGN)
    hdr = bytearray(struct.pack('<I', n))
    for i, nm in enumerate(names):
        hdr += nm.encode('latin1')[:56].ljust(56, b'\x00')
        hdr += struct.pack('<II', offs[i], len(blobs[i]))
    body = bytearray()
    pos = hdr_len
    for i, bb in enumerate(blobs):
        body += b'\x00' * (offs[i] - pos)
        body += bb
        pos = offs[i] + len(bb)
    return bytes(hdr) + bytes(body)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--px', type=int, default=13, help='汉字 em 边长(px)')
    ap.add_argument('--pxsmall', type=int, default=0, help='小字体 em(默认同 --px)')
    ap.add_argument('--pad', type=int, default=0, help='每个 .fnt 尾部填充字节数（内容不变）')
    ap.add_argument('--padrecs', type=int, default=0, help='每个 .fnt 追加的无效记录条数')
    ap.add_argument('--dropjp', action='store_true', help='从 frontend.lmp 删除 japfont*.fnt')
    ap.add_argument('--pxmap', default='', help='覆盖各字体 px，如 gamefonta=13,med=12,...')
    ap.add_argument('--out', default='')
    ap.add_argument('--dry', action='store_true', help='只生成 .fnt/lmp，不重打 ISO')
    a = ap.parse_args()

    hanzi = open(os.path.join(BASE, 'translation', 'jobs', 'zh_top1502.txt'), encoding='utf-8').read()
    punct = open(os.path.join(BASE, 'translation', 'jobs', 'zh_punct.txt'), encoding='utf-8').read()
    print(f'charset: hanzi={len(hanzi)} punct={len(punct)} px={a.px} pad={a.pad} padrecs={a.padrecs} dropjp={a.dropjp}')

    specs = []
    for nm, lmp in (('gamefonta.fnt', 'font'), ('gamefontmed.fnt', 'font'), ('gamefontsmall.fnt', 'font'),
                    ('bigfont.fnt', 'fe'), ('creditfont.fnt', 'fe')):
        specs.append(nm)
    pxof = {'gamefontsmall.fnt': a.pxsmall or a.px}
    for kv in a.pxmap.split(','):
        if '=' in kv:
            k, v = kv.split('=')
            pxof[k.strip()] = int(v)

    # 原始字体来源
    srcs = {}
    orig_font = open(os.path.join(BACK, 'font.lmp'), 'rb').read()
    for nm, off, size in parse_lmp(orig_font)[0]:
        srcs[nm] = orig_font[off:off + size]
    orig_fe = open(os.path.join(BACK, 'frontend.lmp'), 'rb').read()
    fe_ents = parse_lmp(orig_fe)[0]
    for nm, off, size in fe_ents:
        srcs.setdefault(nm, orig_fe[off:off + size])

    built = {}
    for nm in specs:
        p = os.path.join(ANA, f'v17_{nm}')
        open(p, 'wb').write(srcs[nm])
        px = pxof.get(nm, a.px)
        built[nm] = build_font_open(p, os.path.join(ANA, f'v17_{nm}'), px, hanzi, punct,
                                    pad_bytes=a.pad, pad_recs=a.padrecs)

    # font.lmp
    names = [e[0] for e in parse_lmp(orig_font)[0]]
    blobs = [open(os.path.join(ANA, f'v17_{nm}'), 'rb').read() if nm in built else srcs[nm] for nm in names]
    newf = build_lmp(names, blobs)
    # frontend.lmp
    fnames, fblobs = [], []
    for nm, off, size in fe_ents:
        if a.dropjp and nm.startswith('japfont'):
            _c, _h = struct.unpack_from('<HH', srcs[nm], 0)
            _ob = struct.unpack_from('<I', srcs[nm], 0x10)[0]
            _w, _ht = struct.unpack_from('<HH', srcs[nm], _ob)
            _t = (1 << (_w - 1).bit_length()) * (1 << (_ht - 1).bit_length())
            print(f'  frontend: DROP {nm}  file={size}B atlas={_w}x{_ht} tex={_t>>10}KB')
            continue
        fnames.append(nm)
        fblobs.append(open(os.path.join(ANA, f'v17_{nm}'), 'rb').read() if nm in built else srcs[nm])
    newfe = build_lmp(fnames, fblobs)

    tot_tex = sum(v[1] for v in built.values())
    print(f'font.lmp {len(orig_font)} -> {len(newf)}   frontend.lmp {len(orig_fe)} -> {len(newfe)}')
    print(f'5 字体纹理合计(pow2,A8) = {tot_tex/1048576:.2f} MB ;  容器合计 = {(len(newf)+len(newfe))/1048576:.2f} MB')
    open(os.path.join(RES, 'font.lmp'), 'wb').write(newf)
    open(os.path.join(RES, 'frontend.lmp'), 'wb').write(newfe)

    if a.dry:
        print('DRY: 跳过 ISO')
        return
    out = a.out or f'bgda_zh_v17_px{a.px}.iso'
    outp = os.path.join(BASE, out)
    if os.path.exists(outp):
        os.remove(outp)
    exe = os.path.join(BASE, 'extract-xiso-master', 'extract-xiso')
    cmd = [exe, '-c', os.path.basename(os.path.join(BASE, "[XBOX].Baldur's.Gate.Dark.Alliance.[USA]")), out]
    print('mkisofs:', ' '.join(cmd))
    r = subprocess.run(cmd, cwd=BASE, capture_output=True, text=True)
    print(r.stdout[-2000:], r.stderr[-2000:])
    print('iso size', os.path.getsize(outp))


main()
