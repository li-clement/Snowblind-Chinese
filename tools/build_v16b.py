# -*- coding: utf-8 -*-
# v14: 
#  - latin glyphs: copied ORIGINAL pixels (no scaling) keeping orig f5/f6/kern -> baseline aligned
#  - hanzi/punct: rendered in em-box grid (width <= px_h; flat chars keep real height)
#  - charset: top1502 hanzi + punct set from translations
#  - pack: height-grouped rows (latin rows first, then hanzi rows), adaptive row height
#  - font.lmp: gamefonta/med/small replaced; frontend.lmp: bigfont/creditfont/gamefontsmall replaced
import struct, os
from PIL import Image, ImageDraw, ImageFont

BASE = '/Users/lee/code/iso'
RES = os.path.join(BASE, "[XBOX].Baldur's.Gate.Dark.Alliance.[USA]", 'res')
BACK = os.path.join(BASE, 'backup_original')
ANA = os.path.join(BASE, 'analysis')
REC_START = 0x214
TTF = '/System/Library/Fonts/Hiragino Sans GB.ttc'
ALIGN = 0x80
NUM_HANZI = 1502

def parse_lmp(b):
    c = struct.unpack_from('<I', b, 0)[0]
    out = []
    for i in range(c):
        p = 4 + i * 64
        nm = b[p:p + 56].split(b'\x00', 1)[0].decode('latin1')
        off, size = struct.unpack_from('<II', b, p + 56)
        out.append([nm, off, size])
    return out, c

def load_font(path):
    b = open(path, 'rb').read()
    cnt, hgt = struct.unpack_from('<HH', b, 0)
    nsect, magic, offSec, offBmp = struct.unpack_from('<IIII', b, 4)
    atw, ath = struct.unpack_from('<HH', b, offBmp)
    recs = [struct.unpack_from('<8H', b, REC_START + i * 16) for i in range(cnt)]
    pre = b[0x14:REC_START]
    kerning = b[offSec:offBmp]
    meta = b[offBmp + 4: offBmp + 1080]
    start = offBmp + 1080
    return dict(b=b, cnt=cnt, hgt=hgt, nsect=nsect, magic=magic, atw=atw, ath=ath,
                start=start, recs=recs, pre=pre, kerning=kerning, meta=meta)

def extract_glyph_rows(f, v):
    """original-size pixel rows (with 1px pad), trimmed to ink box."""
    x0, x1, y0, y1 = v[1], v[2], v[3], v[4]
    atw, ath, start = f['atw'], f['ath'], f['start']
    x0 = max(0, x0); y0 = max(0, y0)
    x1 = min(x1 + 1, atw); y1 = min(y1 + 1, ath)
    w = x1 - x0; h = y1 - y0
    if w <= 0 or h <= 0:
        return None
    px = [[1 if f['b'][start + yy * atw + xx] > 127 else 0 for xx in range(x0, x1)]
          for yy in range(y0, y1)]
    if not any(any(r) for r in px):
        return None
    ys = [i for i, r in enumerate(px) if any(r)]
    xs = [j for i in range(ys[0], ys[-1] + 1) for j, vv in enumerate(px[i]) if vv]
    ox0, ox1, oy0, oy1 = min(xs), max(xs), ys[0], ys[-1]
    ox0 = max(0, ox0 - 1); ox1 = min(w - 1, ox1 + 1)
    oy0 = max(0, oy0 - 1); oy1 = min(h - 1, oy1 + 1)
    return [row[ox0:ox1 + 1] for row in px[oy0:oy1 + 1]]

def render_em(ch, px_h, ttf):
    """render glyph in an em-box grid: fits within px_h, keeps aspect, min height 2px."""
    big = max(px_h * 4, 32)
    fnt = ImageFont.truetype(ttf, big)
    img = Image.new('L', (big * 2, big * 2), 0)
    ImageDraw.Draw(img).text((big // 2, big // 2), ch, font=fnt, fill=255)
    bb = img.getbbox()
    if not bb:
        return None
    img = img.crop(bb)
    w, h = img.size
    sc = min((px_h - 1) / h, (px_h - 1) / w, 1.0)
    nw = max(1, int(round(w * sc)))
    nh = max(1, int(round(h * sc)))
    if nh < 2:
        sc2 = 2 / h
        nw2 = int(round(w * sc2))
        if nw2 <= px_h:
            nw, nh = max(2, nw2), 2
        else:
            nw, nh = px_h, 2
    nw = min(nw, px_h)
    img = img.resize((nw, nh), Image.LANCZOS)
    canvas = Image.new('L', (px_h, px_h), 0)
    canvas.paste(img, ((px_h - nw) // 2, (px_h - nh) // 2))
    cb = canvas.getbbox()
    if not cb:
        return None
    canvas = canvas.crop(cb)
    px = canvas.load()
    return [[1 if px[x, y] > 100 else 0 for x in range(canvas.size[0])] for y in range(canvas.size[1])]

# 标点墨迹比例 (高/宽 = 相对整角格, vpos=bot基线/top顶部/ctr居中) —— 参考日版 japfontbig0
PUNCT_SPEC = {
  '\u3002': (0.36, 0.34, 'bot'), '\u3001': (0.34, 0.34, 'bot'), '\uff0c': (0.46, 0.34, 'bot'),
  '\uff1a': (0.62, 0.28, 'ctr'), '\uff1b': (0.62, 0.28, 'ctr'), '\uff01': (0.82, 0.32, 'bot'),
  '\uff1f': (0.82, 0.55, 'bot'), '\u201c': (0.52, 0.55, 'top'), '\u201d': (0.52, 0.55, 'top'),
  '\u2018': (0.52, 0.45, 'top'), '\u2019': (0.52, 0.45, 'top'), '\u2026': (0.36, 0.92, 'ctr'),
  '\u2014': (0.18, 0.98, 'ctr'), '\uff08': (0.92, 0.42, 'bot'), '\uff09': (0.92, 0.42, 'bot'),
  '\u300a': (0.66, 0.55, 'bot'), '\u300b': (0.66, 0.55, 'bot'), '\u300c': (0.60, 0.50, 'bot'),
  '\u300d': (0.60, 0.50, 'bot'), '\u3010': (0.90, 0.50, 'bot'), '\u3011': (0.90, 0.50, 'bot'),
  '\u00b7': (0.20, 0.30, 'ctr'),
}
PUNCT_ORDS = {ord(k) for k in PUNCT_SPEC}

def render_punct(ch, px_h, ttf):
    """标点：墨迹按日版比例缩小，放进 px_h 宽 × (px_h-1) 高的整角格内，按基线/顶部/居中
       对齐；墨迹严格落在格内(不串字)。返回 rows(list[list[int]])，与 render_em 同构。"""
    BH = px_h - 1; BW = px_h
    hf, wf, vpos = PUNCT_SPEC.get(ch, (0.70, 0.70, 'bot'))
    big = max(px_h * 8, 96)
    fnt = ImageFont.truetype(ttf, big)
    img = Image.new('L', (big * 2, big * 2), 0)
    ImageDraw.Draw(img).text((big // 2, big // 2), ch, font=fnt, fill=255)
    bb = img.getbbox()
    if not bb:
        return None
    img = img.crop(bb); w, h = img.size
    ih = max(2, round(BH * hf)); iw = max(1, round(BW * wf))
    sc = min(ih / h, iw / w)
    nw = min(iw, max(2, round(w * sc))); nh = min(ih, max(2, round(h * sc)))  # 墨迹最小 2×2，避免细不可读
    img = img.resize((nw, nh), Image.LANCZOS)
    canvas = Image.new('L', (BW, BH), 0)
    ox = (BW - nw) // 2
    oy = BH - nh if vpos == 'bot' else (0 if vpos == 'top' else (BH - nh) // 2)
    if oy < 0:
        oy = 0
    canvas.paste(img, (ox, oy))
    px = canvas.load()
    rows = [[1 if px[x, y] > 100 else 0 for x in range(BW)] for y in range(BH)]
    return rows if any(any(r) for r in rows) else None

def pack_rows(entries, atw):
    """rows can mix glyph heights; row height grows to max glyph in row."""
    placed = []
    x, y = 0, 0
    row_h = 0
    rows_map = {}
    for code, rows in entries:
        if rows is None:
            placed.append((code, None))
            continue
        h = len(rows)
        w = max(len(r) for r in rows) if rows else 0
        if w <= 0 or h <= 0:
            placed.append((code, None))
            continue
        if x + w + 1 > atw:
            x = 0
            y += row_h + 1
            row_h = 0
        if h > row_h:
            row_h = h
        placed.append((code, (x, y, w, h)))
        rows_map[code] = rows
        x += w + 1
    ath = y + row_h + 1 if placed else 0
    atlas = bytearray(atw * ath)
    for code, box in placed:
        if box is None:
            continue
        bx, by, w, h = box
        for yy in range(h):
            for xx, vv in enumerate(rows_map[code][yy]):
                if vv:
                    atlas[(by + yy) * atw + bx + xx] = 255
    return placed, atw, ath, bytes(atlas)

def build_font(src, dst, px_h, hanzi_set, punct_set, max_ath=240):
    f = load_font(src)
    entries = []
    latinmap = {}
    for v in f['recs']:
        c = v[0]
        if c in (0, 0xFFFF) or c == 32:
            continue
        if c in PUNCT_ORDS:      # 让 CJK 标点统一走 render_punct（覆盖原版西文 “ ” … 等）
            continue
        g = extract_glyph_rows(f, v)
        if g is None:
            continue
        entries.append((c, g))
        latinmap[c] = v
    latin_codes = set(latinmap) | {32}
    added = 0
    for ch in hanzi_set:
        if added >= NUM_HANZI:
            break
        c = ord(ch)
        if c in latin_codes:
            continue
        g = render_em(ch, px_h, TTF)
        if g:
            entries.append((c, g))
            added += 1
    for ch in punct_set:
        c = ord(ch)
        if c in latin_codes or any(ec == c for ec, _ in entries):
            continue
        g = render_punct(ch, px_h, TTF)
        if g:
            entries.append((c, g))
    print(f'  {os.path.basename(src)} -> {len(entries)} glyphs (latin {len(latinmap)}, hanzi {added}, punct {len(entries)-len(latinmap)-added})')
    placed, atw, ath, atlas = pack_rows(entries, 1024)
    p2 = (1 << (atw - 1).bit_length(), 1 << (ath - 1).bit_length())
    print(f'    atlas {atw}x{ath} pow2 {p2[0]}x{p2[1]}')
    assert p2[1] <= 256 and ath <= max_ath, f'ath {ath} too tall'
    assert len(placed) == len(entries)
    cnt = len(placed)
    recs = bytearray()
    for c, box in placed:
        if box is None:
            recs += struct.pack('<8H', c, 0, 0, 0, 0, 0, 8, 0xFFFF)
            continue
        bx, by, w, h = box
        if c in latinmap:
            orig = latinmap[c]
            f5, adv, kern = orig[5], orig[6], orig[7]
        else:
            f5, adv, kern = 6, w + 1, 0xFFFF
        recs += struct.pack('<8H', c, bx, bx + w, by, by + h, f5, adv, kern)
    offSec = REC_START + cnt * 16
    offBmp = offSec + len(f['kerning'])
    header = struct.pack('<HHIIII', cnt, 8, f['nsect'], f['magic'], offSec, offBmp)
    out = header + f['pre'] + bytes(recs) + f['kerning']
    out += struct.pack('<HH', atw, ath) + f['meta'] + atlas
    assert len(out) < 0x40000, f'{dst} {len(out)} >= 0x40000'
    open(dst, 'wb').write(out)
    eng_bm = offBmp + 0x38 + 0x400
    act_bm = len(out) - atw * ath
    print(f'    wrote {dst}: {len(out)}B bm_match={eng_bm == act_bm}')
    return cnt

hanzi_set = open(os.path.join(BASE, 'translation', 'jobs', 'zh_top1502.txt'), encoding='utf-8').read()
punct_set = open(os.path.join(BASE, 'translation', 'jobs', 'zh_punct.txt'), encoding='utf-8').read()
print(f'hanzi {len(hanzi_set)} punct {len(punct_set)}: {"".join(punct_set)}')

# font.lmp sources: analysis fonts paths
fonta = os.path.join(ANA, 'gamefonta.fnt')
med   = os.path.join(ANA, 'gamefontmed.fnt')
small = os.path.join(ANA, 'gamefontsmall.fnt')
# if analysis copies missing, extract from backup
import shutil
for p, srclmp, nm in ((fonta, os.path.join(BACK, 'font.lmp'), 'gamefonta.fnt'),
                      (med, os.path.join(BACK, 'font.lmp'), 'gamefontmed.fnt'),
                      (small, os.path.join(BACK, 'font.lmp'), 'gamefontsmall.fnt')):
    if not os.path.exists(p):
        fb = open(srclmp, 'rb').read()
        ents, _ = parse_lmp(fb)
        for enm, eoff, esz in ents:
            if enm == nm:
                open(p, 'wb').write(fb[eoff:eoff + esz])
                break

build_font(fonta, os.path.join(ANA, 'gamefonta_v14.fnt'), 11, hanzi_set, punct_set)
build_font(med,   os.path.join(ANA, 'gamefontmed_v14.fnt'), 11, hanzi_set, punct_set)
build_font(small, os.path.join(ANA, 'gamefontsmall_v14.fnt'), 11, hanzi_set, punct_set)

# ---- frontend: extract original bigfont/creditfont ----
fe = open(os.path.join(BACK, 'frontend.lmp'), 'rb').read()
fents, _ = parse_lmp(fe)
saved = {}
for enm, eoff, esz in fents:
    if enm in ('bigfont.fnt', 'creditfont.fnt'):
        p = os.path.join(ANA, f'orig_{enm}')
        open(p, 'wb').write(fe[eoff:eoff + esz])
        saved[enm] = p
        print(f'extracted {enm}: {esz}B')

bigfont_px = 11  # title/menu: a bit larger
build_font(saved['bigfont.fnt'], os.path.join(ANA, 'bigfont_v14.fnt'), bigfont_px, hanzi_set, punct_set)
build_font(saved['creditfont.fnt'], os.path.join(ANA, 'creditfont_v14.fnt'), 11, hanzi_set, punct_set)

# ---- font.lmp rebuild ----
def build_lmp(names, blobs):
    n = len(names)
    hdr_len = 4 + n * 64
    cur = hdr_len
    if cur % ALIGN:
        cur += ALIGN - (cur % ALIGN)
    offs = []
    for b in blobs:
        offs.append(cur)
        cur += len(b)
        if cur % ALIGN:
            cur += ALIGN - (cur % ALIGN)
    hdr = bytearray(struct.pack('<I', n))
    for i, nm in enumerate(names):
        hdr += nm.encode('latin1')[:56].ljust(56, b'\x00')
        hdr += struct.pack('<II', offs[i], len(blobs[i]))
    body = bytearray()
    pos = hdr_len
    for i, b in enumerate(blobs):
        pad = offs[i] - pos
        assert pad >= 0
        body += b'\x00' * pad
        body += b
        pos = offs[i] + len(b)
    return bytes(hdr) + bytes(body)

orig_font = open(os.path.join(BACK, 'font.lmp'), 'rb').read()
ents, _ = parse_lmp(orig_font)
names = [e[0] for e in ents]
blobs = []
mp = {'gamefonta.fnt': 'gamefonta_v14.fnt', 'gamefontmed.fnt': 'gamefontmed_v14.fnt',
      'gamefontsmall.fnt': 'gamefontsmall_v14.fnt'}
for nm, off, size in ents:
    if nm in mp:
        blobs.append(open(os.path.join(ANA, mp[nm]), 'rb').read())
    else:
        blobs.append(orig_font[off:off + size])
new = build_lmp(names, blobs)
open(os.path.join(RES, 'font.lmp'), 'wb').write(new)
print(f'font.lmp: {len(orig_font)} -> {len(new)}')

# ---- frontend.lmp rebuild ----
names = [e[0] for e in fents]
blobs = []
fmp = {'bigfont.fnt': 'bigfont_v14.fnt', 'creditfont.fnt': 'creditfont_v14.fnt',
       'gamefontsmall.fnt': 'gamefontsmall_v14.fnt'}
for nm, off, size in fents:
    if nm in fmp:
        blobs.append(open(os.path.join(ANA, fmp[nm]), 'rb').read())
    else:
        blobs.append(fe[off:off + size])
newfe = build_lmp(names, blobs)
open(os.path.join(RES, 'frontend.lmp'), 'wb').write(newfe)
print(f'frontend.lmp: {len(fe)} -> {len(newfe)}')
print('DONE v14')