#!/usr/bin/env python3
# fnt_check_v3.py - verify built font with HALF-PIXEL interpretation:
#   glyph top-left = (y//2, x//2); size = (f4-f3)//2 x f6//2
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
        if vals[0] != 0xFFFF and vals[0] != 0:
            recs[vals[0]] = vals
    print(f"{path}: cnt={cnt} hgt={hgt} nsect={nsect} magic=0x{magic:X} atlas={atw}x{ath} recs={len(recs)} ok={len(b)==start+atw*ath}")
    return dict(b=b, atw=atw, ath=ath, start=start, recs=recs)

def show(f, ch, w=24):
    o = ord(ch)
    if o not in f['recs']:
        print(f"  {ch!r} U+{o:04X}: NO REC")
        return
    v = f['recs'][o]
    y, x = v[1] // 2, v[2] // 2
    h = (v[4] - v[3]) // 2 if v[4] > v[3] else 16
    ww = v[6] // 2 if v[6] else w
    b, atw, ath, start = f['b'], f['atw'], f['ath'], f['start']
    print(f"  {ch!r} U+{o:04X} rec=({v[1]},{v[2]},{v[3]},{v[4]},{v[5]},{v[6]}) @pix({y},{x}) size={h}x{ww}")
    for yy in range(y, min(y + h, ath)):
        row = b[start + yy * atw + x: start + yy * atw + x + ww]
        s = ''.join('#' if vv > 127 else ('.' if vv > 0 else ' ') for vv in row)
        print(f"    {yy:03d}|{s}|")

f = load(sys.argv[1])
for c in ['A', 'M', '0', '1', 'Z', '\u4f60', '\u597d', '\u3002', '\uff0c']:
    show(f, c)