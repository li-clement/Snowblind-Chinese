#!/usr/bin/env python3
# fnt_locate.py - find true glyph locations in original atlas, derive f3-f6 semantics
import struct

path = "E:/Game/ps5/iso/analysis/gamefonta.fnt"
b = open(path, 'rb').read()
atw, ath = 256, 158
start = 0xB8C + 1080

def ink_at(y, x):
    if y < 0 or y >= ath or x < 0 or x >= atw: return 0
    return b[start + y*atw + x] > 127

def scan(y, x, r=24):
    """find ink bbox within r of (y,x); return (miny,maxy,minx,maxx) or None"""
    ys, xs = [], []
    for yy in range(max(0, y-r), min(ath, y+r+1)):
        for xx in range(max(0, x-r), min(atw, x+r+1)):
            if ink_at(yy, xx):
                ys.append(yy); xs.append(xx)
    if not ys: return None
    return (min(ys), max(ys), min(xs), max(xs))

cnt, hgt = struct.unpack_from('<HH', b, 0)
offSec, offBmp = struct.unpack_from('<IIII', b, 12)[0], struct.unpack_from('<IIII', b, 12)[2]
recStart = offSec - cnt*16
print(f"{'ch':<4s} {'rec(y,x,f3..f6)':<32s} {'hpix(y,x)':<12s} {'ink bbox(y..y,x..x)':<24s} {'offset(dy,dx)'}")
for i in range(cnt):
    o = recStart + i*16
    v = struct.unpack_from('<8H', b, o)
    c = v[0]
    if not (32 <= c < 127) or v[0] in (0, 0xFFFF):
        continue
    y, x = v[1]//2, v[2]//2
    bb = scan(y, x)
    if bb is None:
        print(f"{chr(c):<4s} {str(v[1:7]):<32s} ({y},{x}){'':12s} NO INK nearby")
        continue
    my, My, mx, Mx = bb
    print(f"{chr(c):<4s} {str(v[1:7]):<32s} ({y:3d},{x:3d})  y {my:3d}..{My:3d} x {mx:3d}..{Mx:3d}   dy={my-y} dx={mx-x}")