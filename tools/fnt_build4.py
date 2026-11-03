#!/usr/bin/env python3
# fnt_build4.py - CJK font rebuild, atlas WIDTH configurable (default 1024 like japfontbig0)
#   fixes vs fnt_build3:
#     - atlas width parameter (--atw), default 1024
#     - zh record f3-f6 as HALF-PIXEL window (0, px_h*2, 0, wpx*2) matching original
#       latin records like 'A'=(y0=20,y1=36,x0=6,x1=16) with px_h=8
# usage: fnt_build4.py <in.fnt> <out.fnt> <px_h> [--atw N] [ttf]
import struct, os, sys, argparse
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
    pre = b[0x14:REC_START]
    kerning = b[offSec:offBmp]
    meta = b[offBmp + 4: offBmp + 4 + 1076]
    return dict(b=b, cnt=cnt, hgt=hgt, nsect=nsect, magic=magic, atw=atw, ath=ath,
                start=offBmp + 1080, recs=recs, pre=pre, kerning=kerning, meta=meta)

def extract_glyph(f, vals):
    """cut glyph from original atlas. record coords are HALF-PIXELS (probe: digit
    records 152-232 all exceed atlas height 158; /2 = 76-116 fits; 'Z' 0,14 -> 0,7
    renders perfect). So pixel pos = (vals[1]//2, vals[2]//2).
    Keep fnt_build3's proven extraction window logic verbatim."""
    y, x = vals[1] // 2, vals[2] // 2
    hh = max(4, vals[4] - vals[3])
    ww = max(4, vals[6])
    atw, ath, start = f['atw'], f['ath'], f['start']
    win_w = min(max(ww + 2, 12), atw - x)
    win_h = min(max(hh + 2, 12), ath - y)
    if win_w <= 0 or win_h <= 0:
        return None
    px = [[1 if bv > 127 else 0 for bv in
           f['b'][start + (y + yy) * atw + x: start + (y + yy) * atw + x + win_w]]
          for yy in range(win_h)]
    if not any(any(r) for r in px):
        return None
    ys = [i for i, r in enumerate(px) if any(r)]
    xs = [j for i in range(ys[0], ys[-1] + 1) for j, v in enumerate(px[i]) if v]
    x0, x1, y0, y1 = min(xs), max(xs), ys[0], ys[-1]
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
    ap = argparse.ArgumentParser()
    ap.add_argument('src'); ap.add_argument('dst'); ap.add_argument('px_h', type=int)
    ap.add_argument('--atw', type=int, default=1024)
    ap.add_argument('--ttf', default=r'C:\Windows\Fonts\msyh.ttc')
    a = ap.parse_args()
    f = load_font(a.src)

    charset_file = os.path.join(os.path.dirname(os.path.dirname(a.dst)), 'translation', 'jobs', 'zh_charset.txt')
    charset = open(charset_file, encoding='utf-8').read() if os.path.exists(charset_file) else ''
    have = set(v[0] for v in f['recs'] if v[0] != 0xFFFF)
    need = sorted({ord(ch) for ch in charset if ord(ch) not in have and ch not in '\n\r\t'})
    print(f"need {len(need)} zh glyphs")

    entries = []
    fallback = []
    for v in f['recs']:
        c = v[0]
        if c == 0xFFFF or c == 0:
            continue
        g = extract_glyph(f, v)
        if g is None:
            fallback.append(c)
            continue
        entries.append((c, g, v))
    print(f"extracted {len(entries)}/{f['cnt']} original glyphs; fallback {len(fallback)}: {''.join(chr(c) for c in fallback)}")
    for o in fallback:
        g = render_cjk(chr(o), a.px_h, a.ttf)
        if g:
            entries.append((o, g, None))
    for o in need:
        g = render_cjk(chr(o), a.px_h, a.ttf)
        if g:
            entries.append((o, g, None))
    print(f"total {len(entries)} glyphs")

    atw = a.atw
    pos, atw2, ath, atlas = pack_atlas(entries, atw)
    print(f"atlas {atw2}x{ath}")

    bycode = {code: (x, y) for code, rows, x, y in pos}
    named = {v[0]: v for v in f['recs'] if v[0] != 0xFFFF and v[0] != 0}
    recs = bytearray()
    for code, rows, x, y in sorted(pos, key=lambda t: t[0]):
        wpx = max(len(r) for r in rows) if rows else 4
        if code in named and named[code][3] != 0xFFFF:
            ov = named[code]
            # keep original f3-f6; y/x are half-pixels already (x2 of atlas px)
            recs += struct.pack('<8H', code, y * 2, x * 2, ov[3], ov[4], ov[5], ov[6], 0xFFFF)
        else:
            # zh: half-pixel window covering full glyph
            recs += struct.pack('<8H', code, y * 2, x * 2, 0, a.px_h * 2, 0, wpx * 2, 0xFFFF)
    cnt = len(pos)

    offSec = REC_START + cnt * 16
    offBmp = offSec + len(f['kerning'])
    header = struct.pack('<HHIIII', cnt, a.px_h, f['nsect'], f['magic'], offSec, offBmp)
    out = header + f['pre'] + bytes(recs) + f['kerning']
    out += struct.pack('<HH', atw2, ath) + f['meta'] + atlas
    open(a.dst, 'wb').write(out)
    print(f"wrote {a.dst}: {len(out)} bytes (cnt={cnt} px_h={a.px_h} atlas={atw2}x{ath})")

if __name__ == '__main__':
    main()