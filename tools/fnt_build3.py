#!/usr/bin/env python3
# fnt_build3.py - CONSERVATIVE font rebuild:
#   keep ALL original static regions byte-identical (pre-legacy 0x14..0x100,
#   0x100..0x214 legacy, kerning region, 1080B metadata, nsect/magic values),
#   keep original 141 records' f3..f6 fields untouched (only y/x updated to new
#   atlas positions), append zh glyph records, atlas width stays 256.
# usage: fnt_build3.py <in.fnt> <out.fnt> <px_h> [ttf]
import struct, os, sys
from PIL import Image, ImageDraw, ImageFont

REC_START = 0x214

def load_font(path):
    b = open(path, 'rb').read()
    cnt, hgt = struct.unpack_from('<HH', b, 0)
    nsect, magic, offSec, offBmp = struct.unpack_from('<IIII', b, 4)
    atw, ath = struct.unpack_from('<HH', b, offBmp)
    recStart = offSec - cnt * 16
    assert recStart == REC_START, f"recStart=0x{recStart:X}"
    recs = []
    for i in range(cnt):
        recs.append(struct.unpack_from('<8H', b, recStart + i * 16))
    pre = b[0x14:REC_START]               # 0x14..0x214 verbatim (incl legacy 0x100..0x214)
    kerning = b[offSec:offBmp]
    meta = b[offBmp + 4: offBmp + 4 + 1076]   # 1076B metadata (atlas starts at offBmp+1080)
    return dict(b=b, cnt=cnt, hgt=hgt, nsect=nsect, magic=magic, atw=atw, ath=ath,
                start=offBmp + 1080, recs=recs, pre=pre, kerning=kerning, meta=meta)

def extract_glyph(f, vals, atw, ath, start):
    """cut glyph from original atlas. Record coords are HALF-PIXELS (probe: digit
    records 152-232 all exceed atlas height 158; /2 = 76-116 fits; 'Z' 0,14 -> 0,7
    renders perfect). So pixel pos = (vals[1]//2, vals[2]//2)."""
    y, x = vals[1] // 2, vals[2] // 2
    # f3-f6 are PIXEL units (not half-px): f4-f3 = glyph height, f6 = glyph width
    hh = max(4, vals[4] - vals[3])
    ww = max(4, vals[6])
    win_w = min(max(ww + 2, 12), atw - x)
    win_h = min(max(hh + 2, 12), ath - y)
    if win_w <= 0 or win_h <= 0:
        return None
    px = [[1 if b_val > 127 else 0 for b_val in
           f['b'][start + (y + yy) * atw + x: start + (y + yy) * atw + x + win_w]]
          for yy in range(win_h)]
    if not any(any(r) for r in px):
        return None
    ys = [i for i, r in enumerate(px) if any(r)]
    xs = [j for i in range(ys[0], ys[-1] + 1) for j, v in enumerate(px[i]) if v]
    x0, x1, y0, y1 = min(xs), max(xs), ys[0], ys[-1]
    # 1px pad
    x0 = max(0, x0 - 1); x1 = min(win_w - 1, x1 + 1)
    y0 = max(0, y0 - 1); y1 = min(win_h - 1, y1 + 1)
    return [row[x0:x1 + 1] for row in px[y0:y1 + 1]]

def render_cjk(ch, px_h, ttf):
    big = px_h * 8
    fnt = ImageFont.truetype(ttf, big)
    img = Image.new('L', (big * 2, big * 2), 0)
    d = ImageDraw.Draw(img)
    d.text((big // 2, big // 2), ch, font=fnt, fill=255)
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

def pack_atlas(glyphs, atw):
    """glyphs: list of (code, rows, orig_record). returns (positions, atw, ath, bytes)"""
    x, y, row_h = 0, 0, 0
    pos = []
    for code, rows, _ov in glyphs:
        h = len(rows)
        w = max(len(r) for r in rows)
        if x + w + 1 > atw:
            x = 0
            y += row_h + 1
            row_h = 0
        pos.append((code, rows, x, y))
        x += w + 1
        row_h = max(row_h, h)
    ath = y + row_h + 1
    atlas = bytearray(atw * ath)
    for code, rows, bx, by in pos:
        for yy, row in enumerate(rows):
            for xx, v in enumerate(row):
                if v:
                    atlas[(by + yy) * atw + bx + xx] = 255
    return pos, atw, ath, bytes(atlas)

def main():
    src, dst = sys.argv[1], sys.argv[2]
    px_h = int(sys.argv[3])
    ttf = sys.argv[4] if len(sys.argv) > 4 else r'C:\Windows\Fonts\msyh.ttc'
    f = load_font(src)

    charset_file = os.path.join(os.path.dirname(os.path.dirname(dst)), 'translation', 'jobs', 'zh_charset.txt')
    charset = open(charset_file, encoding='utf-8').read() if os.path.exists(charset_file) else ''
    have = set(v[0] for v in f['recs'] if v[0] != 0xFFFF)
    need = []
    for ch in charset:
        o = ord(ch)
        if o not in have and ch not in '\n\r\t':
            need.append(o)
    need = sorted(set(need))

    # 1) extract original glyphs (keep ink, new atlas pos)
    entries = []
    for v in f['recs']:
        c = v[0]
        if c == 0xFFFF or c == 0:
            continue
        g = extract_glyph(f, v, f['atw'], f['ath'], f['start'])
        if g is None:
            continue
        entries.append((c, g, v))     # code, rows, original record
    print(f"extracted {len(entries)}/{f['cnt']} original glyphs")
    # 2) zh glyphs
    for o in need:
        g = render_cjk(chr(o), px_h, ttf)
        if g is None:
            continue
        entries.append((o, g, None))
    print(f"added {len(entries) - sum(1 for _, _, v in entries if v)} zh glyphs; total {len(entries)}")

    atw = f['atw']                     # keep 256
    pos, atw2, ath, atlas = pack_atlas(entries, atw)
    print(f"atlas {atw2}x{ath}")

    # build records sorted by charcode; record coordinates are HALF-PIXELS (x2 of atlas px)
    bycode = {}
    for code, rows, x, y in pos:
        bycode[code] = (x, y)
    named = {v[0]: v for v in f['recs'] if v[0] != 0xFFFF and v[0] != 0}
    recs = bytearray()
    for code, rows, x, y in sorted(pos, key=lambda t: t[0]):
        wpx = max(len(r) for r in rows) if rows else 4
        if code in named and named[code][3] != 0xFFFF:
            ov = named[code]
            recs += struct.pack('<8H', code, y * 2, x * 2, ov[3], ov[4], ov[5], ov[6], 0xFFFF)
        else:
            # zh template in PIXEL units: height = px_h, width = wpx
            recs += struct.pack('<8H', code, y * 2, x * 2, 0, px_h, 0, wpx, 0xFFFF)
    cnt = len(pos)

    offSec = REC_START + cnt * 16
    offBmp = offSec + len(f['kerning'])
    header = struct.pack('<HHIIII', cnt, px_h, f['nsect'], f['magic'], offSec, offBmp)
    out = header + f['pre'] + bytes(recs) + f['kerning']
    out += struct.pack('<HH', atw2, ath) + f['meta'] + atlas
    open(dst, 'wb').write(out)
    print(f"wrote {dst}: {len(out)} bytes (cnt={cnt} px_h={px_h} atlas={atw2}x{ath})")

if __name__ == '__main__':
    main()