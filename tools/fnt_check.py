#!/usr/bin/env python3
# fnt_check.py - parse a built .fnt, render sample glyphs as ASCII art
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
        c = vals[0]
        if c != 0xFFFF and c != 0:
            recs[c] = vals
    print(f"{path}: cnt={cnt} hgt={hgt} atlas={atw}x{ath} recStart=0x{recStart:X} offBmp=0x{offBmp:X} recs={len(recs)}")
    return dict(b=b, atw=atw, ath=ath, start=start, recs=recs)

def render(f, c, w=22):
    if ord(c) not in f['recs']:
        print(f"  {c!r}: NO RECORD")
        return
    vals = f['recs'][ord(c)]
    y, x = vals[1] // 2, vals[2] // 2
    b, atw, ath, start = f['b'], f['atw'], f['ath'], f['start']
    rows = []
    y1 = y
    while y1 < ath:
        row = b[start + y1*atw + x: start + y1*atw + x + w]
        if not any(row):
            break
        rows.append(''.join('#' if v > 127 else ('.' if v > 0 else ' ') for v in row))
        y1 += 1
        if len(rows) > 26:
            break
    print(f"  {c!r} U+{ord(c):04X} @({y},{x}) f={vals[3:7]}: " + ('(empty)' if not rows else ''))
    for r in rows:
        print(f"    |{r}|")

f = load(sys.argv[1])
samples = ['A', 'B', '你', '好', '世', '界', '传', '游', '。', '，', '%', '5']
if len(sys.argv) > 2:
    samples = sys.argv[2]
for c in samples:
    render(f, c)