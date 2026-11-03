#!/usr/bin/env python3
# fnt_grid.py - cluster ink in original atlas, map to records, verify 16px grid
import struct

path = "E:/Game/ps5/iso/analysis/gamefonta.fnt"
b = open(path, 'rb').read()
atw, ath = 256, 158
start = 0xB8C + 1080
cnt, hgt = struct.unpack_from('<HH', b, 0)
offSec, offBmp = struct.unpack_from('<IIII', b, 12)[0], struct.unpack_from('<IIII', b, 12)[2]
recStart = offSec - cnt*16

# 1. find all ink pixels
ink = set()
for yy in range(ath):
    for xx in range(atw):
        if b[start + yy*atw + xx] > 127:
            ink.add((yy, xx))
print(f"ink pixels: {len(ink)}")

# 2. cluster 8-connected
clusters = []
seen = set()
for p in ink:
    if p in seen: continue
    stack = [p]; seen.add(p); comp = []
    while stack:
        y, x = stack.pop(); comp.append((y, x))
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                q = (y+dy, x+dx)
                if q in ink and q not in seen:
                    seen.add(q); stack.append(q)
    if len(comp) >= 4:
        ys = [c[0] for c in comp]; xs = [c[1] for c in comp]
        clusters.append((min(ys), max(ys), min(xs), max(xs), len(comp)))
clusters.sort()
print(f"clusters: {len(clusters)}")
for c in clusters:
    print(f"  bbox y {c[0]:3d}..{c[1]:3d} x {c[2]:3d}..{c[3]:3d} ink={c[4]}")

# 3. record coords (half-px) for ascii
print("\nrecords (half-px):")
recs = {}
for i in range(cnt):
    o = recStart + i*16
    v = struct.unpack_from('<8H', b, o)
    if 32 <= v[0] < 127:
        recs[v[0]] = v
for c in range(32, 127):
    if c in recs:
        v = recs[c]
        print(f"  {chr(c):<3s} rec_hpx=({v[1]//2},{v[2]//2}) f3-6=({v[3]},{v[4]},{v[5]},{v[6]})")