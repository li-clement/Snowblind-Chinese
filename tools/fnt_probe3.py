#!/usr/bin/env python3
# fnt_probe3.py - for each char, render window at BOTH (y,x) and (y/2,x/2) interpretations
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
        print(f"{c!r}: no rec")
        continue
    v = f['recs'][o]
    print(f"===== {c!r} rec=({v[0]},{v[1]},{v[2]},{v[3]},{v[4]},{v[5]},{v[6]}) =====")
    for label, y, x in [('pix', v[1], v[2]), ('half', v[1] // 2, v[2] // 2)]:
        b, atw, ath, start = f['b'], f['atw'], f['ath'], f['start']
        if y < 0 or x < 0 or y + 14 > ath or x + 24 > atw:
            print(f"  [{label}] ({y},{x}) OUT")
            continue
        print(f"  [{label}] @({y},{x}):")
        for yy in range(y, min(y + 14, ath)):
            row = b[start + yy * atw + x: start + yy * atw + x + 24]
            s = ''.join('#' if vv > 127 else ('.' if vv > 0 else ' ') for vv in row)
            print(f"    {yy:03d}|{s}|")