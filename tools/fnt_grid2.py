#!/usr/bin/env python3
# fnt_grid2.py - fine clustering (threshold >40) and systematic record->cluster matching
import struct

path = "E:/Game/ps5/iso/analysis/gamefonta.fnt"
b = open(path, 'rb').read()
atw, ath = 256, 158
start = 0xB8C + 1080
cnt, hgt = struct.unpack_from('<HH', b, 0)
offSec, offBmp = struct.unpack_from('<IIII', b, 12)[0], struct.unpack_from('<IIII', b, 12)[2]
recStart = offSec - cnt*16

TH = 40
pix = {}
for yy in range(ath):
    for xx in range(atw):
        v = b[start + yy*atw + xx]
        if v > TH:
            pix[(yy, xx)] = v

# cluster 8-connected
clusters = []
seen = set()
for p in pix:
    if p in seen: continue
    stack = [p]; seen.add(p); comp = []
    while stack:
        y, x = stack.pop(); comp.append((y, x))
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                q = (y+dy, x+dx)
                if q in pix and q not in seen:
                    seen.add(q); stack.append(q)
    if len(comp) >= 6:
        ys = [c[0] for c in comp]; xs = [c[1] for c in comp]
        clusters.append((min(ys), max(ys), min(xs), max(xs), len(comp)))
clusters.sort(key=lambda c: (c[0]//16, c[2]//16))
print(f"clusters: {len(clusters)}")
for c in clusters:
    print(f"  y {c[0]:3d}..{c[1]:3d} x {c[2]:3d}..{c[3]:3d} ink={c[4]}")

# match each ascii record (hpx) to nearest cluster center
def dist(ry, rx, c):
    cy = (c[0]+c[1])/2; cx = (c[2]+c[3])/2
    return abs(ry-cy)+abs(rx-cx)
print("\n=== records -> nearest cluster ===")
for i in range(cnt):
    o = recStart + i*16
    v = struct.unpack_from('<8H', b, o)
    c = v[0]
    if not (32 <= c < 127) or c in (0, 0xFFFF):
        continue
    ry, rx = v[1]//2, v[2]//2
    best = min(clusters, key=lambda cl: dist(ry, rx, cl))
    d = dist(ry, rx, best)
    dy = ry - (best[0]+best[1])//2
    dx = rx - (best[2]+best[3])//2
    print(f"  {chr(c):<3s} rec=({ry:3d},{rx:3d}) -> y {best[0]:3d}..{best[1]:3d} x {best[2]:3d}..{best[3]:3d} d={d:4.1f} (dy={dy:+.1f} dx={dx:+.1f})")