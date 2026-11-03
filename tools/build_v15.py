#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v15 —— 修两个问题（根因均已实测确认）

A) "标点很大 / 一 偏大"
   v14 装箱只留 1px 间隙，且 rect 紧贴墨迹。引擎按 rect(x0,x1,y0,y1) **1:1** 采样图集
   像素（DrawChars 0x67580），邻格墨迹会被一起画出来：实测 v14 gamefonta 有
   1382/1653 个字形 rect 内混入邻居墨迹 —— "。"因此像撑满整格的圆环。
   → v15：拉丁**原样搬回原本图集矩形**（原版重叠对数=0，本就无冲突）；
     CJK/标点放进**另一段 x 区间**的规则网格，格间强制空白列+空白行，永不串字。

B) "中文字号太小"
   v14 CJK ink 只有 9~10px（拉丁大写 13px）。图集高度有硬上限：引擎在 FSet(0x65DB0)
   要求 log2(atw)/log2(ath) < 0x1e，且 pow2 尺寸需 ≤256 → **ath ≤ 255**。
   关键技巧：拉丁只占 x∈[0,256)，把 atw 扩到 2048 后，x∈[256,2048) 整条区域是空的，
   CJK 网格可与拉丁**共用同一高度区间**，于是 em 上限从 ~10 提到 16。
     atw=2048, cell=em+1(空白列), 行间留 1 空白行 → em=16: per_row=105, rows=15, ath=255 ✔
   → 汉字 ink 从 9~10px 提升到 16px（≈ +60%），与拉丁大写(13px)协调。

标点：按日版 japfontbig0 比例缩小 ink（。ink 8px/24 cell ≈ 0.33），
      横画类（一、—）宽度限制在 0.8em 以内，不再横跨整格显得过大。
拉丁：像素与 rect 逐位照搬，度量 f5/adv/kern 沿用原版 → 基线对齐不变。
"""
import struct, os
from PIL import Image, ImageDraw, ImageFont

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES  = os.path.join(BASE, "[XBOX].Baldur's.Gate.Dark.Alliance.[USA]", 'res')
BACK = os.path.join(BASE, 'backup_original')
ANA  = os.path.join(BASE, 'analysis')
TR   = os.path.join(BASE, 'translation', 'jobs')

REC_START = 0x214
ALIGN     = 0x80
MAX_ATH   = 255            # 图集高度硬上限（pow2 ≤ 256）
ATW       = 2048           # 拉丁只占 x<256，其余给 CJK 网格

TTF_CANDIDATES = [
    r'C:\Windows\Fonts\msyh.ttc',
    '/System/Library/Fonts/Hiragino Sans GB.ttc',
    '/System/Library/Fonts/STHeiti Medium.ttc',
]

# 标点 ink 高 / em —— **直接取自日版 true_japfontbig0.fnt（cell=24）实测**：
#   。7x8 → h/em=0.33 | ！3x19 → 0.79 | ？13x19 → 0.79 | 一 20x3 → w/em=0.83, h/em=0.125
#   （v15 早期用自拟的 0.34 给"！/？"，结果只有 1px 宽、完全不可读）
PUNCT_H = {'。': 0.34, '，': 0.34, '、': 0.32, '！': 0.79, '？': 0.79, '：': 0.71,
           '“': 0.42, '”': 0.42, '…': 0.30, '—': 0.16, '《': 0.55, '》': 0.55,
           '「': 0.45, '」': 0.45}
# 标点 ink 宽 / em：横画类保持"长而细"，但必须 < 1.0 才能完整落进 rect（否则被裁断）
PUNCT_W = {'—': 0.94, '…': 0.94, '一': 0.83, '。': 0.42, '，': 0.42, '、': 0.38,
           '：': 0.38, '！': 0.38, '「': 0.45, '」': 0.45}

def pick_ttf():
    for p in TTF_CANDIDATES:
        if os.path.exists(p): return p
    raise SystemExit('no CJK ttf found')

TTF = pick_ttf()

# ------------------------------------------------------------------ .fnt format
def load_font(path):
    b = open(path, 'rb').read()
    cnt, hgt = struct.unpack_from('<HH', b, 0)
    nsect, magic, offSec, offBmp = struct.unpack_from('<IIII', b, 4)
    atw, ath = struct.unpack_from('<HH', b, offBmp)
    recs = [struct.unpack_from('<8H', b, REC_START + i * 16) for i in range(cnt)]
    return dict(b=b, cnt=cnt, hgt=hgt, nsect=nsect, magic=magic, atw=atw, ath=ath,
                start=offBmp + 1080, recs=recs, pre=b[0x14:REC_START],
                kerning=b[offSec:offBmp], meta=b[offBmp + 4: offBmp + 1080])

def latin_pixels(f, v):
    x0, x1, y0, y1 = v[1], v[2], v[3], v[4]
    if x1 <= x0 or y1 <= y0 or x1 > f['atw'] or y1 > f['ath']: return None
    atw, start = f['atw'], f['start']
    rows = [[1 if f['b'][start + yy * atw + xx] > 127 else 0 for xx in range(x0, x1)]
            for yy in range(y0, y1)]
    if not any(any(r) for r in rows): return None
    return x0, y0, x1 - x0, y1 - y0, rows

# ------------------------------------------------------------------ CJK raster
def raster(ch, em, max_w=None):
    """按 TTF 原始比例栅格化，使墨迹**长边**贴合 em（细笔画不会被拉成实心方块）。"""
    big = max(em * 8, 64)
    fnt = ImageFont.truetype(TTF, big)
    img = Image.new('L', (big * 2, big * 2), 0)
    ImageDraw.Draw(img).text((big // 2, big // 2), ch, font=fnt, fill=255)
    bb = img.getbbox()
    if not bb: return None
    img = img.crop(bb)
    w, h = img.size
    scale = em / max(w, h)                     # 等比：长边贴合 em
    nw = max(1, int(round(w * scale)))
    nh = max(1, int(round(h * scale)))
    if max_w is not None and nw > max_w:       # 仅收窄宽度，不改变高度
        img = img.resize((max_w, nh), Image.LANCZOS)
        px = img.load()
        return [[1 if px[x, y] > 96 else 0 for x in range(max_w)] for y in range(nh)]
    img = img.resize((nw, nh), Image.LANCZOS)
    px = img.load()
    return [[1 if px[x, y] > 96 else 0 for x in range(nw)] for y in range(nh)]

def raster_h(ch, ink_h, max_w=None):
    """按**高度**为准等比栅格化（用于窄高的标点：！、？、：）。
    与 raster() 的区别：raster() 锁长边，会把 ratio<1 的窄字形压成 1px 宽。"""
    big = max(ink_h * 8, 64)
    fnt = ImageFont.truetype(TTF, big)
    img = Image.new('L', (big * 2, big * 2), 0)
    ImageDraw.Draw(img).text((big // 2, big // 2), ch, font=fnt, fill=255)
    bb = img.getbbox()
    if not bb: return None
    img = img.crop(bb)
    w, h = img.size
    nw = max(1, int(round(w * ink_h / h)))
    if max_w is not None and nw > max_w: nw = max_w
    img = img.resize((nw, ink_h), Image.LANCZOS)
    px = img.load()
    return [[1 if px[x, y] > 96 else 0 for x in range(nw)] for y in range(ink_h)]

def place(rows, rect_w, baseline_y, pad_w, pad_h):
    """把 ink 放进空白格内，**保证墨迹完全落在 rect[0,rect_w)×[0,baseline_y+1) 内**：
    水平居中、墨迹底边贴基线 baseline_y（与拉丁大写一致）。
    格总尺寸 = (rect_w+pad_w)×(rect_h+pad_h)，多出的 pad 列/行永远空白 → 不串字。"""
    rect_h = baseline_y + 1
    canvas = [[0] * (rect_w + pad_w) for _ in range(max(rect_h, baseline_y + 1) + pad_h)]
    h = len(rows); w = max(len(r) for r in rows)
    if h > baseline_y + 1:                  # 墨迹超出基线时截断（正常不会发生）
        rows = rows[h - (baseline_y + 1):]; h = baseline_y + 1
    oy = baseline_y + 1 - h                 # 底边对齐 rect 底
    ox = (rect_w - w) // 2
    if ox < 0: ox = 0
    for yy in range(h):
        for xx, vv in enumerate(rows[yy]):
            if vv and ox + xx < rect_w:
                canvas[oy + yy][ox + xx] = 1
    return canvas

# ------------------------------------------------------------------ build one font
def build_font(src_path, dst_path, em, hanzi, punct, verbose=True):
    f = load_font(src_path)
    atw = ATW
    ath_lat = f['ath']

    # ---- 拉丁：原矩形逐像素照搬（x<256 区域）
    latin_recs = []
    for v in f['recs']:
        c = v[0]
        if c in (0, 0xFFFF) or c == 32: continue
        lp = latin_pixels(f, v)
        if lp is None: continue
        latin_recs.append(v)

    have = {v[0] for v in latin_recs} | {32}

    # ---- CJK/标点：x∈[256, atw) 的独立网格，与拉丁共用高度区间
    cell_w = em + 1          # 格宽 = rect(em) + 1 空白列（隔离带）
    x_base = 256
    per_row = (atw - x_base) // cell_w

    entries = []
    # 基线对齐（全部实测自原版/日版）：
    #   拉丁大写 A/T/H ink 底 = rect 顶+14；小写 x/n +12；句点 . +3
    #   日版汉字 ink 高 21/24，top_pad=1 bot_pad=2 → 几乎满框、底贴基线
    #   日版"一"ink 20x3 / cell 24，top_off=9 bot_off=12 → **垂直居中**（细横不贴基线）
    # CJK rect 统一 em×em，格高 em+1（底部 1 空白行隔离），墨迹保证完整落在 rect 内。
    CAP_LINE = em - 2        # 汉字/大写级基线（底部留 2px，与原版 A 一致）

    def put(code, rws, line):
        h = len(rws); w = max(len(r) for r in rws)
        if w > em or h > em: return
        entries.append((code, place(rws, em, line, 1, em + 1 - line)))
        have.add(code)

    def add(ch, line=None, size=None):
        c = ord(ch)
        if c in have: return
        tgt = size if size is not None else em
        rws = raster(ch, tgt)
        if not rws: return
        put(c, rws, CAP_LINE if line is None else line)

    # 汉字：满框（视觉字号 = em）；"一"单独处理
    for ch in hanzi:
        if ch == '一': continue
        add(ch)

    # "一"：日版实测 ink 20x3 / cell 24 → 宽 0.83em、垂直居中。
    # 若贴基线会显得又扁又靠下（v15 早期版本的问题）。
    c = ord('一')
    if c not in have:
        rws = raster('一', em, max_w=int(round(em * PUNCT_W['一'])))
        if rws: put(c, rws, (em + len(rws)) // 2)

    # 标点：分三类处理，避免"长边锁定"把窄字形压扁。
    #   · 横画类（—…）本身很扁 → raster() 锁长边即得"长而细"，再限宽不超 rect，垂直居中
    #   · 方/圆点类（。，、：）→ 按高度缩小到日版比例，贴 x-height 基线
    #   · 窄高类（！？）→ raster_h 按高度缩放，宽度按比例保留
    for ch in punct:
        c = ord(ch)
        if c in have: continue
        if ch in ('—', '…'):
            rws = raster(ch, em, max_w=int(round(em * PUNCT_W[ch])))
            line = (em + len(rws)) // 2 if rws else CAP_LINE
        else:
            ink_h = max(5, int(round(em * PUNCT_H.get(ch, 0.45))))
            rws = raster_h(ch, ink_h, max_w=em)
            line = em - 3 if ch in '。、，：；' else CAP_LINE
        if not rws: continue
        put(c, rws, line)

    row_h  = em + 1                          # rect(em) + 1 空白行

    n_rows = (len(entries) + per_row - 1) // per_row
    ath = max(ath_lat, n_rows * row_h)
    assert ath <= MAX_ATH, f'{os.path.basename(src_path)}: ath={ath} > {MAX_ATH}'

    # 图集：先按最终 ath 分配，再写入拉丁与 CJK
    atlas = bytearray(atw * ath)
    for v in latin_recs:
        x0, y0, w, h, rows = latin_pixels(f, v)
        for yy, row in enumerate(rows):
            base = (y0 + yy) * atw + x0
            for xx, vv in enumerate(row):
                if vv: atlas[base + xx] = 255

    cjk_recs = []
    for i, (code, grid) in enumerate(entries):
        rr = i // per_row; cc = i % per_row
        bx = x_base + cc * cell_w; by = rr * row_h
        for yy in range(row_h):
            base = (by + yy) * atw + bx
            row = grid[yy]
            for xx in range(cell_w):
                if row[xx]: atlas[base + xx] = 255
        # f5=0（与日版大字体一致：cell 顶即参考线），adv = em（全宽前进）
        cjk_recs.append((code, bx, bx + em, by, by + em, 0, em, 0xFFFF))

    recs_out = latin_recs + cjk_recs

    # ---- 硬校验：图集里每一个墨迹像素都必须落在某个 rect 内。
    #      （v14 的"标点/一 显得过大"正是因为 rect 里混入邻格墨迹；这里反向杜绝。）
    in_rect = bytearray(atw * ath)
    for v in recs_out:
        if v[1] >= v[2] or v[3] >= v[4]: continue
        for yy in range(v[3], min(v[4], ath)):
            for xx in range(v[1], min(v[2], atw)):
                in_rect[yy * atw + xx] = 1
    stray = sum(1 for i, p in enumerate(atlas) if p > 127 and not in_rect[i])
    assert stray == 0, f'{os.path.basename(src_path)}: {stray} ink px outside every rect'

    cnt = len(recs_out)
    p2w = 1 << (atw - 1).bit_length(); p2h = 1 << (ath - 1).bit_length()
    if verbose:
        print(f'  {os.path.basename(src_path)}: em={em} latin={len(latin_recs)} '
              f'cjk={len(cjk_recs)} cnt={cnt} atlas={atw}x{ath} pow2={p2w}x{p2h}')

    out = bytearray()
    offSec = REC_START + cnt * 16
    offBmp = offSec + len(f['kerning'])
    out += struct.pack('<HHIIII', cnt, f['hgt'], f['nsect'], f['magic'], offSec, offBmp)
    out += f['pre']
    for r in recs_out: out += struct.pack('<8H', *r)
    out += f['kerning']
    out += struct.pack('<HH', atw, ath) + f['meta'] + bytes(atlas[:atw * ath])
    open(dst_path, 'wb').write(bytes(out))
    eng_bm = offBmp + 0x38 + 0x400
    act_bm = len(out) - atw * ath
    if verbose:
        print(f'    wrote {os.path.basename(dst_path)}: {len(out)}B bm_match={eng_bm == act_bm}')
    return out

# ------------------------------------------------------------------ lmp helpers
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
    hdr = bytearray(struct.pack('<I', n))
    cur = 4 + n * 64
    offs = []
    for bl in blobs:
        offs.append(cur); cur += len(bl)
    for i, nm in enumerate(names):
        nb = nm.encode('latin1')[:56]
        hdr += nb.ljust(56, b'\x00') + struct.pack('<II', offs[i], len(blobs[i]))
    body = bytes(hdr) + b''.join(blobs)
    return body + b'\x00' * ((-len(body)) % ALIGN)

# ------------------------------------------------------------------ main
EM_MAP = {'gamefonta.fnt': 16, 'gamefontmed.fnt': 16, 'gamefontsmall.fnt': 16,
          'bigfont.fnt': 16, 'creditfont.fnt': 16}

def main():
    hanzi = open(os.path.join(TR, 'zh_top1502.txt'), encoding='utf-8').read()
    punct = open(os.path.join(TR, 'zh_punct.txt'), encoding='utf-8').read()
    print(f'TTF={TTF} hanzi={len(hanzi)} punct={len(punct)}: {punct}')

    made = {}
    for nm, em in EM_MAP.items():
        blob_src = os.path.join(BACK, 'frontend.lmp') if nm in ('bigfont.fnt', 'creditfont.fnt') \
                   else os.path.join(BACK, 'font.lmp')
        bb = open(blob_src, 'rb').read()
        ents, _ = parse_lmp(bb)
        orig = None
        for e_nm, off, size in ents:
            if e_nm == nm: orig = bb[off:off + size]; break
        assert orig, f'{nm} not in {blob_src}'
        tmp = os.path.join(ANA, f'_orig_{nm}')
        open(tmp, 'wb').write(orig)
        dst = os.path.join(ANA, nm.replace('.fnt', '_v15.fnt'))
        build_font(tmp, dst, em, hanzi, punct)
        made[nm] = dst

    for lmp in ('font.lmp', 'frontend.lmp'):
        p = os.path.join(RES, lmp)
        cur = open(p, 'rb').read()
        ents, _ = parse_lmp(cur)
        names, blobs = [], []
        for nm, off, size in ents:
            names.append(nm)
            blobs.append(open(made[nm], 'rb').read() if nm in made else cur[off:off + size])
        new = build_lmp(names, blobs)
        open(p, 'wb').write(new)
        print(f'{lmp}: {len(cur)} -> {len(new)}')
    print('DONE v15')

if __name__ == '__main__':
    main()
