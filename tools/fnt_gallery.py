#!/usr/bin/env python3
# fnt_gallery.py - render glyph gallery under (y/2,x/2) vs (y,x) to verify coordinates
# usage: python fnt_gallery.py <file.fnt> [half|raw] [chars...]
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
    return dict(cnt=cnt, hgt=hgt, atw=atw, ath=ath, start=start, b=b, recs=recs)

def main():
    path = sys.argv[1]
    mode = sys.argv[2] if len(sys.argv) > 2 else 'half'
    chars = sys.argv[3] if len(sys.argv) > 3 else '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,!?:;()[]+-*/%&'
    f = load(path)
    b, start, atw, ath, hgt = f['b'], f['start'], f['atw'], f['ath'], f['hgt']
    print(f"mode={mode}  atlas {atw}x{ath}")
    for c in chars:
        if ord(c) not in f['recs']:
            continue
        r = f['recs'][ord(c)]
        y1, x1 = r[1], r[2]
        if mode == 'half':
            y, x = y1 // 2, x1 // 2
        else:
            y, x = y1, x1
        if y < 0 or x < 0 or y + hgt > ath:
            print(f"{c!r}({y1},{x1})->({y},{x}): OUT")
            continue
        rows = []
        for rr in range(y, y + hgt):
            row = b[start + rr*atw + x : start + rr*atw + x + 16]
            rows.append(''.join('#' if v > 127 else ('.' if v > 0 else ' ') for v in row))
        print(f"{c!r} ({y1},{x1})->({y},{x}):")
        for rr, s in zip(range(y, y+hgt), rows):
            print(f"  {rr:03d}|{s}|")

if __name__ == '__main__':
    main()