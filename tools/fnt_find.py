#!/usr/bin/env python3
# fnt_find.py - template-match a system-rendered char against the atlas to locate real glyph position
import struct, sys
from PIL import Image, ImageDraw, ImageFont

def load(path):
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
            recs[vals[0]] = vals
    return dict(b=b, atw=atw, ath=ath, start=start, recs=recs)

def ref_template(ch, h=14):
    size = h * 6
    fnt = ImageFont.truetype(r'C:\Windows\Fonts\arialbd.ttf', int(h * 3.2))
    img = Image.new('L', (size, size), 0)
    d = ImageDraw.Draw(img)
    d.text((size // 8, size // 8), ch, font=fnt, fill=255)
    bbox = img.getbbox()
    img = img.crop(bbox)
    w, hh = img.size
    sc = h / hh
    nw = max(1, int(round(w * sc)))
    img = img.resize((nw, h), Image.LANCZOS)
    px = img.load()
    return [[1 if px[x, y] > 100 else 0 for x in range(nw)] for y in range(h)]

def match(f, tmpl):
    b, atw, ath, start = f['b'], f['atw'], f['ath'], f['start']
    th, tw = len(tmpl), len(tmpl[0])
    tn = sum(sum(r) for r in tmpl)
    best = []
    for y in range(0, ath - th + 1):
        for x in range(0, atw - tw + 1):
            inter = 0
            for yy in range(th):
                row = b[start + (y + yy) * atw + x: start + (y + yy) * atw + x + tw]
                for xx in range(tw):
                    if tmpl[yy][xx] and row[xx] > 127:
                        inter += 1
            if inter > 0:
                best.append((inter, y, x))
    best.sort(reverse=True)
    return best[:6]

f = load(sys.argv[1])
for ch in sys.argv[2]:
    rec = f['recs'].get(ord(ch))
    print(f"--- {ch!r} record: {rec[1:7] if rec else 'NONE'} ---")
    tmpl = ref_template(ch)
    for inter, y, x in match(f, tmpl):
        print(f"   match={inter} @({y},{x})  (raw/2: y={rec[1]//2} x={rec[2]//2} raw={rec[1]},{rec[2]})")