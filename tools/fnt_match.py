#!/usr/bin/env python3
# fnt_match.py - find the correct atlas-coordinate interpretation by IoU vs reference renderings
# usage: python fnt_match.py <file.fnt>
import struct, sys, math
from PIL import Image, ImageDraw, ImageFont

SIMPLIFIED = list('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,!?:;()[]+-*/#%&')

def load_font(path):
    b = open(path, 'rb').read()
    cnt, hgt = struct.unpack_from('<HH', b, 0)
    nsect, magic, offSec, offBmp = struct.unpack_from('<IIII', b, 4)
    atw, ath = struct.unpack_from('<HH', b, offBmp)
    start = offBmp + 1080
    recStart = offSec - cnt * 16
    recs = {}
    for i in range(cnt):
        o = recStart + i * 16
        vals = struct.unpack_from('<8H', b, o)
        if vals[0] != 0xFFFF:
            recs.setdefault(vals[0], []).append(vals)
    return dict(cnt=cnt, hgt=hgt, atw=atw, ath=ath, start=start, b=b, recs=recs)

def extract(f, c, y, x, wbox=14):
    b, atw, ath, start = f['b'], f['atw'], f['ath'], f['start']
    hgt = f['hgt']
    if y < 0 or x < 0 or y + hgt > ath or x + wbox > atw:
        return None
    out = []
    for r in range(y, y + hgt):
        row = b[start + r*atw + x : start + r*atw + x + wbox]
        out.append([1 if v > 127 else 0 for v in row])
    return out

def ref_glyph(c, px_h, wbox=14):
    fonts = [
        r'C:\Windows\Fonts\arialbd.ttf',
        r'C:\Windows\Fonts\arial.ttf',
        r'C:\Windows\Fonts\simhei.ttf',
    ]
    for fp in fonts:
        try:
            size = int(px_h * 2.2)
            fnt = ImageFont.truetype(fp, size)
            img = Image.new('L', (int(wbox*2.4), int(px_h*2.6)), 0)
            d = ImageDraw.Draw(img)
            d.text((2, 1), c, font=fnt, fill=255)
            img = img.resize((wbox, px_h), Image.LANCZOS)
            px = img.load()
            g = [[1 if px[x, y] > 80 else 0 for x in range(wbox)] for y in range(px_h)]
            return g
        except Exception:
            continue
    return None

def iou(a, b, shift=0):
    H = min(len(a), len(b))
    W = min(len(a[0]), len(b[0]))
    inter = union = 0
    for y in range(H):
        for x in range(W):
            bb = b[y][x]
            if shift:
                aa = a[y][(x - shift) % W] if False else a[y][x]
            inter += 1 if (a[y][x] and bb) else 0
            union += 1 if (a[y][x] or bb) else 0
    return inter / union if union else 0.0

def main():
    path = sys.argv[1]
    f = load_font(path)
    print(f"font: hgt={f['hgt']} atlas={f['atw']}x{f['ath']} recs={len(f['recs'])}")

    interps = ['yx', 'xy', 'yx/2', 'xy/2']
    for c in SIMPLIFIED:
        if ord(c) not in f['recs']:
            continue
        rec = f['recs'][ord(c)][0]
        y1, x1, f3, f4 = rec[1], rec[2], rec[3], rec[4]
        ref = ref_glyph(c, f['hgt'])
        if not ref:
            continue
        best = ('', -1)
        for name, yy, xx in [('yx', y1, x1), ('xy', x1, y1),
                             ('yx/2', y1//2, x1//2), ('xy/2', x1//2, y1//2),
                             ('f3f4', f3, f4), ('f3f4/2', f3//2, f4//2)]:
            g = extract(f, c, yy, xx)
            if not g:
                sc = -2
            else:
                sc = max(iou(g, ref) for _ in [0])
                # also try 1..2 px shifts
                sc = max(sc, iou(g, ref))
            if sc > best[1]:
                best = (name, sc)
        print(f"{c!r}: rec=({y1},{x1},{f3},{f4}) best={best[0]} ioU={best[1]:.2f}", end='')
        # show density under 'yx'
        g = extract(f, c, y1, x1, wbox=14)
        if g:
            n = sum(sum(r) for r in g)
            print(f"  yx-density={n}", end='')
        print()

if __name__ == '__main__':
    main()