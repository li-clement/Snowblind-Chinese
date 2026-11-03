#!/usr/bin/env python3
# fnt_measure.py - precise glyph bbox + record fields for a char across all fonts
import struct, os, sys

ANALYSIS = r'E:\Game\ps5\iso\analysis'

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
    return dict(b=b, atw=atw, ath=ath, start=start, recs=recs, recStart=recStart, cnt=cnt)

def measure(f, c):
    if ord(c) not in f['recs']:
        return None
    vals = f['recs'][ord(c)]
    y, x = vals[1] // 2, vals[2] // 2
    b, atw, ath, start = f['b'], f['atw'], f['ath'], f['start']
    # find precise ink bbox in a generous window
    if y < 0 or x < 0 or y >= ath or x >= atw:
        return (vals, None)
    win_h = min(64, ath - y)
    win_w = min(64, atw - x)
    rows = []
    for r in range(win_h):
        row = b[start + (y + r) * atw + x: start + (y + r) * atw + x + win_w]
        rows.append([v > 0 for v in row])
    ys = [r for r in range(win_h) if any(rows[r])]
    if not ys:
        return (vals, (0, 0, 0, 0))
    y0, y1 = ys[0], ys[-1]
    xs = [c for r in ys for c, v in enumerate(rows[r]) if v]
    x0, x1 = min(xs), max(xs)
    return (vals, (y0, y1, x0, x1))

for fname in ['gamefonta.fnt', 'gamefontmed.fnt', 'gamefontsmall.fnt', 'bigfont.fnt', 'creditfont.fnt', 'japfontbig0.fnt', 'japfontsmall0.fnt']:
    f = load(os.path.join(ANALYSIS, fname))
    print(f"\n== {fname} (atlas {f['atw']}x{f['ath']}, cnt {f['cnt']}) ==")
    for c in ['A', 'M', 'W', 'i', '0', 'a', '.', ' ']:
        r = measure(f, c)
        if r is None:
            print(f"  {c!r}: not in font")
            continue
        vals, box = r
        if box is None:
            print(f"  {c!r}: rec={vals[1:]}; OOB y,x={vals[1]//2},{vals[2]//2}")
        else:
            y0, y1, x0, x1 = box
            print(f"  {c!r}: rec f1..f6={vals[1:7]}  ink box y={y0}..{y1} x={x0}..{x1}  => {x1-x0+1}x{y1-y0+1}px @pix({vals[1]//2}, {vals[2]//2})")