# -*- coding: utf-8 -*-
# v13: fix render_cjk vertical-stretch bug (caused SOLID BLOCK glyphs for flat chars like 一),
#      variable-width atlas packing (no overlap for wide glyphs),
#      records use exact glyph box (y0=vy, y1=vy+h, no empty padding),
#      char set = top1502 hanzi (99.4% coverage).
import struct, os
from PIL import Image, ImageDraw, ImageFont

BASE = r'E:\Game\ps5\iso'
RES = os.path.join(BASE, "[XBOX].Baldur's.Gate.Dark.Alliance.[USA]", 'res')
BACK = os.path.join(BASE, 'backup_original')
ANA = os.path.join(BASE, 'analysis')
REC_START = 0x214
TTF = r'C:\Windows\Fonts\msyh.ttc'
ALIGN = 0x80
NUM_HANZI = 1502

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

def extract_glyph(f, v):
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

def rows_to_img(rows):
    h = len(rows); w = max(len(r) for r in rows) if rows else 0
    im = Image.new('L', (w, h), 0)
    for y, row in enumerate(rows):
        for x, vv in enumerate(row):
            if vv:
                im.putpixel((x, y), 255)
    return im

def normalize_rows(rows, target_h):
    im = rows_to_img(rows)
    w, h = im.size
    if h == 0 or w == 0:
        return None
    sc = target_h / h
    nw = max(1, int(round(w * sc)))
    if nw > target_h * 2:
        nw = target_h * 2
    im = im.resize((nw, target_h), Image.LANCZOS)
    px = im.load()
    return [[1 if px[x, y] > 100 else 0 for x in range(nw)] for y in range(target_h)]

def render_cjk(ch, px_h, ttf):
    """FIXED: resize to (nw, round(target_h)) so flat glyphs keep their real height."""
    big = px_h * 8
    try:
        fnt = ImageFont.truetype(ttf, big)
    except Exception:
        return None
    img = Image.new('L', (big * 2, big * 2), 0)
    ImageDraw.Draw(img).text((big // 2, big // 2), ch, font=fnt, fill=255)
    bbox = img.getbbox()
    if not bbox:
        return None
    img = img.crop(bbox)
    w, h = img.size
    ratio = h / big
    target_h = max(px_h * ratio, px_h * 35 // 100)
    if target_h > px_h:
        target_h = px_h
    sc = target_h / h
    nw = max(1, int(round(w * sc)))
    if nw > px_h * 2:
        nw = px_h * 2
    th = max(1, int(round(target_h)))
    img = img.resize((nw, th), Image.LANCZOS)
    px = img.load()
    return [[1 if px[x, y] > 100 else 0 for x in range(nw)] for y in range(th)]

def pack_atlas(entries, atw, step):
    """variable-width packing; row height = step (>= max glyph h +1). returns placed boxes at exact glyph pos."""
    placed = []
    x, y = 0, 0
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
            y += step
        placed.append((code, (x, y, w, h)))
        rows_map[code] = rows
        x += w + 1
    ath = y + step
    atlas = bytearray(atw * ath)
    for code, box in placed:
        if box is None:
            continue
        bx, by, w, h = box
        rows = rows_map[code]
        vy = by + (step - h) // 2          # vertical center in slot
        for yy in range(h):
            for xx, vv in enumerate(rows[yy]):
                if vv:
                    atlas[(vy + yy) * atw + bx + xx] = 255
    # convert to exact boxes (vy based) for records
    exact = []
    for code, box in placed:
        if box is None:
            exact.append((code, None))
            continue
        bx, by, w, h = box
        vy = by + (step - h) // 2
        exact.append((code, (bx, vy, w, h)))
    return exact, atw, ath, bytes(atlas)

def build_font(src, dst, px_h, hanzi_set, max_ath=240):
    f = load_font(src)
    step = px_h + 1
    entries = []
    sc_map = {}
    for v in f['recs']:
        c = v[0]
        if c in (0, 0xFFFF) or c == 32:
            continue
        g = extract_glyph(f, v)
        if g is None:
            continue
        gh = len(g)
        g = normalize_rows(g, px_h)
        if g is None:
            continue
        sc_map[c] = px_h / gh if gh else 1.0
        entries.append((c, g))
    latin_codes = {c for c, _ in entries} | {32}
    added = 0
    for ch in hanzi_set:
        if added >= NUM_HANZI:
            break
        c = ord(ch)
        if c in latin_codes:
            continue
        g = render_cjk(ch, px_h, TTF)
        if g:
            entries.append((c, g))
            added += 1
    print(f'  {os.path.basename(src)} -> {len(entries)} glyphs (latin {len(entries)-added}, hanzi {added})')
    placed, atw, ath, atlas = pack_atlas(entries, 1024, step)
    p2 = (1 << (atw - 1).bit_length(), 1 << (ath - 1).bit_length())
    print(f'    atlas {atw}x{ath} pow2 {p2[0]}x{p2[1]}  (step {step})')
    assert p2[1] <= 256 and ath <= max_ath, f'ath {ath} too tall'
    assert len(placed) == len(entries)
    cnt = len(placed)
    recs = bytearray()
    for c, box in placed:
        if box is None:
            recs += struct.pack('<8H', c, 0, 0, 0, 0, 0, 8, 0xFFFF)
            continue
        bx, vy, w, h = box
        orig = None
        for v in f['recs']:
            if v[0] == c:
                orig = v
                break
        if orig is not None and orig[0] != 32:
            sc = sc_map.get(c, 1.0)
            f5 = orig[5]
            adv = max(w + 1, int(round(orig[6] * sc))) if orig[6] else w + 1
            kern = orig[7]
        else:
            f5 = 6
            adv = w + 1
            kern = 0xFFFF
        recs += struct.pack('<8H', c, bx, bx + w, vy, vy + h, f5, adv, kern)
    offSec = REC_START + cnt * 16
    offBmp = offSec + len(f['kerning'])
    header = struct.pack('<HHIIII', cnt, 8, f['nsect'], f['magic'], offSec, offBmp)
    out = header + f['pre'] + bytes(recs) + f['kerning']
    out += struct.pack('<HH', atw, ath) + f['meta'] + atlas
    open(dst, 'wb').write(out)
    eng_bm = offBmp + 0x38 + 0x400
    act_bm = len(out) - atw * ath
    print(f'    wrote {dst}: {len(out)}B bm_match={eng_bm == act_bm}')
    return cnt

hanzi_set = open(os.path.join(BASE, 'translation', 'jobs', 'zh_top1502.txt'), encoding='utf-8').read()

build_font(os.path.join(ANA, 'gamefonta.fnt'),  os.path.join(ANA, 'gamefonta_v13.fnt'),  10, hanzi_set)
build_font(os.path.join(ANA, 'gamefontmed.fnt'), os.path.join(ANA, 'gamefontmed_v13.fnt'), 9, hanzi_set)
build_font(os.path.join(ANA, 'gamefontsmall.fnt'), os.path.join(ANA, 'gamefontsmall_v13.fnt'), 8, hanzi_set)

# ---- font.lmp rebuild ----
def parse_lmp(b):
    c = struct.unpack_from('<I', b, 0)[0]
    out = []
    for i in range(c):
        pp = 4 + i * 64
        nm = b[pp:pp + 56].split(b'\x00', 1)[0].decode('latin1')
        off, size = struct.unpack_from('<II', b, pp + 56)
        out.append([nm, off, size])
    return out, c

def build(names, blobs):
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
ents, c = parse_lmp(orig_font)
names = [e[0] for e in ents]
blobs = []
mp = {'gamefonta.fnt': 'gamefonta_v13.fnt', 'gamefontmed.fnt': 'gamefontmed_v13.fnt',
      'gamefontsmall.fnt': 'gamefontsmall_v13.fnt'}
for nm, off, size in ents:
    if nm in mp:
        blobs.append(open(os.path.join(ANA, mp[nm]), 'rb').read())
    else:
        blobs.append(orig_font[off:off + size])
new = build(names, blobs)
open(os.path.join(RES, 'font.lmp'), 'wb').write(new)
print(f'font.lmp: {len(orig_font)} -> {len(new)}')

front = open(os.path.join(BACK, 'frontend.lmp'), 'rb').read()
open(os.path.join(RES, 'frontend.lmp'), 'wb').write(front)
print('frontend.lmp original')
print('DONE v13')