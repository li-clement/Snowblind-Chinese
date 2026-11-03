#!/usr/bin/env python3
# fnt_check5.py - verify v5 font: sample glyphs from atlas using engine semantics (f1..f4 = half-px rect)
import struct, sys

def load(path):
    b = open(path, 'rb').read()
    cnt, hgt = struct.unpack_from('<HH', b, 0)
    nsect, magic, offSec, offBmp = struct.unpack_from('<IIII', b, 4)
    atw, ath = struct.unpack_from('<HH', b, offBmp)
    recStart = offSec - cnt * 16
    recs = [struct.unpack_from('<8H', b, recStart + i * 16) for i in range(cnt)]
    start = offBmp + 1080
    return b, cnt, hgt, atw, ath, recs, start

def sample(b, atw, ath, start, v):
    # engine atlas rect: x0=f1, x1=f2, y0=f3, y1=f4 (ABSOLUTE PIXELS)
    x0, x1 = v[1], v[2]
    y0, y1 = v[3], v[4]
    x1 = min(x1, atw); y1 = min(y1, ath)
    w = x1 - x0; h = y1 - y0
    if w <= 0 or h <= 0:
        return None
    return [[b[start + yy*atw + xx] for xx in range(x0, x1)] for yy in range(y0, y1)]

def show(px, label, th=127):
    print(f'  {label} ({len(px)}x{len(px[0]) if px else 0})')
    for r in px[:24]:
        print('   |' + ''.join('#' if v > th else ('+' if v > 40 else '.') for v in r) + '|')

def main(path, chars):
    b, cnt, hgt, atw, ath, recs, start = load(path)
    print(f'{path}: cnt={cnt} hgt={hgt} atlas={atw}x{ath} size={len(b)}')
    found = {}
    for v in recs:
        if v[0] in chars and v[0] not in found:
            found[v[0]] = v
    for c in chars:
        v = found.get(c)
        if not v:
            print(f'  {chr(c)!r}: NOT FOUND')
            continue
        px = sample(b, atw, ath, start, v)
        if px is None:
            print(f'  {chr(c)!r} rec={v[1:7]} : zero rect (space-like)')
            continue
        show(px, f'{chr(c)!r} U+{c:04X} rec=({v[1]},{v[2]},{v[3]},{v[4]},{v[5]},{v[6]})')

if __name__ == '__main__':
    path = sys.argv[1]
    chars = [ord(x) for x in sys.argv[2]] if len(sys.argv) > 2 else [ord(x) for x in 'AZ09az.你中文']
    main(path, chars)