#!/usr/bin/env python3
# glyph_compare.py - dump glyph bitmap from original and rebuilt atlas for a char
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
        v = struct.unpack_from('<8H', b, o)
        if v[0] != 0xFFFF and v[0] != 0:
            recs[v[0]] = v
    return dict(b=b, atw=atw, ath=ath, start=start, recs=recs, hgt=hgt, cnt=cnt)

def dump_glyph(f, ch, w=14):
    c = ord(ch)
    if c not in f['recs']:
        print(f"  {ch!r}: NO REC")
        return
    v = f['recs'][c]
    y, x = v[1] // 2, v[2] // 2
    hh = max(1, (v[4] - v[3]) // 2)
    ww = max(1, v[6] // 2)
    hh = min(hh, f['ath'] - y)
    ww = min(ww, f['atw'] - x)
    print(f"  {ch!r} U+{c:04X} rec=({v[1]},{v[2]},{v[3]},{v[4]},{v[5]},{v[6]}) @pix({y},{x}) size={hh}x{ww}")
    for yy in range(y, min(y + hh, f['ath'])):
        row = f['b'][f['start'] + yy * f['atw'] + x: f['start'] + yy * f['atw'] + x + ww]
        s = ''.join('#' if bv > 127 else '.' for bv in row)
        print(f"    {yy:03d}|{s}|")

for path, label in [("E:/Game/ps5/iso/analysis/gamefonta.fnt", "ORIG"), ("E:/Game/ps5/iso/analysis/gamefonta_v4.fnt", "V4")]:
    f = load(path)
    print(f"===== {label}: cnt={f['cnt']} hgt={f['hgt']} atlas={f['atw']}x{f['ath']} =====")
    for ch in ['0', 'A', 'M', 'a', 'g', ' ', '!', '.', 'Z']:
        dump_glyph(f, ch)
    print()