#!/usr/bin/env python3
# fnt_table_dump.py - dump original font records sorted by slot and charcode
import struct, sys

path = "E:/Game/ps5/iso/analysis/gamefonta.fnt"
b = open(path, 'rb').read()
cnt, hgt = struct.unpack_from('<HH', b, 0)
nsect, magic, offSec, offBmp = struct.unpack_from('<IIII', b, 4)
atw, ath = struct.unpack_from('<HH', b, offBmp)
start = offBmp + 1080
recStart = offSec - cnt * 16
print(f"cnt={cnt} hgt={hgt} atlas={atw}x{ath} recStart=0x{recStart:X} offSec=0x{offSec:X} offBmp=0x{offBmp:X}")
print("\n== records by SLOT (order in file) ==")
for i in range(cnt):
    o = recStart + i * 16
    v = struct.unpack_from('<8H', b, o)
    c = v[0]
    nm = chr(c) if 32 <= c < 127 else f'U+{c:04X}'
    print(f"  slot{i:3d} char={nm:<6s} rec=({v[1]},{v[2]},{v[3]},{v[4]},{v[5]},{v[6]},{v[7]}) ypx={v[1]//2} xpx={v[2]//2}")
print("\n== ASCII digits area scan: find non-empty glyphs in atlas ==")
# scan whole atlas for ink and report bounding blocks
import collections
ink_rows = []
for yy in range(ath):
    row = b[start + yy * atw: start + yy * atw + atw]
    if any(x > 127 for x in row):
        ink_rows.append(yy)
print(f"atlas height {ath}, ink rows: {len(ink_rows)} (first 160: {ink_rows[:160]})")
# For each ASCII record, compute the ink bbox in its window
print("\n== ink bbox within each ASCII record window (half-px) ==")
for i in range(cnt):
    o = recStart + i * 16
    v = struct.unpack_from('<8H', b, o)
    c = v[0]
    if not (32 <= c < 127):
        continue
    y, x = v[1] // 2, v[2] // 2
    hh = max(1, (v[4] - v[3]) // 2)
    ww = max(1, v[6] // 2)
    cnt_ink = 0
    xs = []
    ys_ = []
    for yy in range(y, min(y + hh, ath)):
        row = b[start + yy * atw + x: start + yy * atw + min(x + ww, atw)]
        for xx, val in enumerate(row):
            if val > 127:
                cnt_ink += 1
                xs.append(x + xx)
                ys_.append(yy)
    nm = chr(c) if 32 <= c < 127 else f'U+{c:04X}'
    if cnt_ink:
        print(f"  {nm:<3s} rec=({v[1]},{v[2]},{v[3]},{v[4]},{v[5]},{v[6]}) window@({y},{x}) {hh}x{ww} ink={cnt_ink} bbox=({min(xs)},{min(ys_)})-({max(xs)},{max(ys_)})")
    else:
        print(f"  {nm:<3s} rec=({v[1]},{v[2]},{v[3]},{v[4]},{v[5]},{v[6]}) window@({y},{x}) {hh}x{ww} ink=0  <-- EMPTY")