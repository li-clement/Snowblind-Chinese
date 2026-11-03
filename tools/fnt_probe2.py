#!/usr/bin/env python3
# fnt_probe2.py - verify glyph size hypothesis: h=(f4-f3), w=f6 (pixels), cut at (y/2, x/2)
import struct, sys

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

f = load(sys.argv[1])
for c in sys.argv[2:]:
    o = ord(c)
    if o not in f['recs']:
        print(f"{c!r}: no record")
        continue
    v = f['recs'][o]
    y, x = v[1] // 2, v[2] // 2
    h = v[4] - v[3]
    w = v[6]
    b, atw, ath, start = f['b'], f['atw'], f['ath'], f['start']
    print(f"{c!r} rec={v[1:7]} -> pix({y},{x}) size h={h} w={w}")
    for yy in range(y, min(y + h, ath)):
        row = b[start + yy * atw + x: start + yy * atw + x + w]
        s = ''.join('#' if vv > 127 else ('.' if vv > 0 else ' ') for vv in row)
        print(f"  {yy:03d}|{s}|")