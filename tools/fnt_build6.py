#!/usr/bin/env python3
# fnt_build6.py - v8 fonts: force pow2 atlas <= 1024x512 (uniform 15px glyphs, 16px step)
import struct, os, sys
from PIL import Image, ImageDraw, ImageFont

REC_START = 0x214
PX_H = 15          # all glyphs scaled to this height
STEP = 16          # 15px + 1px gap
ATW = 1024

def load_font(path):
    b = open(path, 'rb').read()
    cnt, hgt = struct.unpack_from('<HH', b, 0)
    nsect, magic, offSec, offBmp = struct.unpack_from('<IIII', b, 4)
    atw, ath = struct.unpack_from('<HH', b, offBmp)
    recStart = offSec - cnt * 16
    assert recStart == REC_START
    recs = [struct.unpack_from('<8H', b, recStart + i * 16) for i in range(cnt)]
    pre = b[0x14:REC_START]
    kerning = b[offSec:offBmp]
    meta = b[offBmp + 4: offBmp + 1080]
    return dict(b=b, cnt=cnt, hgt=hgt, nsect=nsect, magic=magic, atw=atw, ath=ath,
                start=offBmp + 1080, recs=recs, pre=pre, kerning=kerning, meta=meta)

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

def img_to_rows(im, keep):
    w, h = im.size
    px = im.load()
    rows = []
    for y in range(h):
        row = []
        for x in range(w):
            row.append(1 if (im.getpixel((x, y)) > 100 if isinstance(im.getpixel((x, y)), int) else im.getpixel((x,y))[0] > 100) else 0)
        rows.append(row)
    return rows

def normalize_rows(rows, target_h=PX_H):
    """scale glyph rows so height == target_h, width capped at target_h*2"""
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
    img = img.resize((nw, px_h), Image.LANCZOS)
    px = img.load()
    return [[1 if px[x, y] > 100 else 0 for x in range(nw)] for y in range(px_h)]

def pack_atlas(entries, atw=ATW, step=STEP):
    """entries: list of (code, rows). fixed row height step; place 1px-gap columns."""
    placed = []
    x, y = 0, 0
    rows_map = {}
    for code, rows in entries:
        if rows is None:
            placed.append((code, None))
            continue
        h = len(rows); w = max(len(r) for r in rows)
        if w <= 0 or h <= 0:
            placed.append((code, None))
            continue
        if x + w + 1 > atw:
            x = 0
            y += step
        placed.append((code, (x, y, w, h)))
        rows_map[code] = rows
        x += step
    ath = y + step
    atlas = bytearray(atw * ath)
    for code, box in placed:
        if box is None:
            continue
        bx, by, w, h = box
        rows = rows_map[code]
        vy = by + (step - h)  # bottom-align? no - center
        vy = by + (step - h) // 2
        for yy in range(h):
            for xx, vv in enumerate(rows[yy]):
                if vv:
                    atlas[(vy + yy) * atw + bx + xx] = 255
    return placed, atw, ath, bytes(atlas)

def main():
    src, dst = sys.argv[1], sys.argv[2]
    ttf = sys.argv[3] if len(sys.argv) > 3 else r'C:\Windows\Fonts\msyh.ttc'
    f = load_font(src)
    cs_file = os.path.join(r'E:\Game\ps5\iso\translation', 'jobs', 'zh_charset.txt')
    charset = open(cs_file, encoding='utf-8').read() if os.path.exists(cs_file) else ''
    have = set(v[0] for v in f['recs'] if v[0] not in (0, 0xFFFF))
    need = sorted({ord(ch) for ch in charset if ord(ch) not in have and ch not in '\n\r\t'})

    entries = []
    fallback = []
    sc_map = {}   # code -> scale factor for f5/f6 scaling
    for v in f['recs']:
        c = v[0]
        if c in (0, 0xFFFF):
            continue
        if c == 32:
            entries.append((32, None))
            continue
        g = extract_glyph(f, v)
        if g is None:
            fallback.append(c)
            continue
        gh = len(g)
        g = normalize_rows(g)
        if g is None:
            fallback.append(c)
            continue
        sc_map[c] = PX_H / gh if gh else 1.0
        entries.append((c, g))
    print(f'extracted {len(entries)}/{f["cnt"]}; fallback {len(fallback)}')

    for c in fallback:
        g = render_cjk(chr(c), PX_H, ttf)
        if g:
            entries.append((c, g))
    for o in need:
        g = render_cjk(chr(o), PX_H, ttf)
        if g:
            entries.append((o, g))
    print(f'total {len(entries)} glyphs')

    placed, atw, ath, atlas = pack_atlas(entries)
    print(f'atlas {atw}x{ath}; pow2={1 << (atw - 1).bit_length()}x{1 << (ath - 1).bit_length()}')
    assert ath <= 512, f'atlas height {ath} > 512!'

    recs = bytearray()
    posmap = {c: box for c, box in placed}
    cnt = len(placed)
    for c, box in placed:
        if c == 32 and box is None:
            recs += struct.pack('<8H', c, 0, 0, 0, 0, 0, 8, 0xFFFF)
            continue
        if box is None:
            recs += struct.pack('<8H', c, 0, 0, 0, 0, 0, 8, 0xFFFF)
            continue
        bx, by, w, h = box
        # find original record for latin glyphs to scale f5/f6
        orig = None
        for v in f['recs']:
            if v[0] == c:
                orig = v
                break
        if orig is not None and orig[0] != 32:
            sc = sc_map.get(c, 1.0)
            f5 = orig[5]  # baseline offset is absolute screen px - keep original
            adv = max(w + 2, int(round(orig[6] * sc))) if orig[6] else w + 2
            kern = orig[7]
        else:
            f5 = 6
            adv = w + 2
            kern = 0xFFFF
        recs += struct.pack('<8H', c, bx, bx + w, by, by + h, f5, adv, kern)

    offSec = REC_START + cnt * 16
    offBmp = offSec + len(f['kerning'])
    header = struct.pack('<HHIIII', cnt, 8, f['nsect'], f['magic'], offSec, offBmp)  # hgt=8
    out = header + f['pre'] + bytes(recs) + f['kerning']
    out += struct.pack('<HH', atw, ath) + f['meta'] + atlas
    open(dst, 'wb').write(out)
    print(f'wrote {dst}: {len(out)}B cnt={cnt} hgt=8 atlas={atw}x{ath}')

if __name__ == '__main__':
    main()