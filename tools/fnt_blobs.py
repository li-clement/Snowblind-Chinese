#!/usr/bin/env python3
# fnt_blobs.py - connected-ink analysis of a .fnt atlas; correlate blobs with record coords
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
            recs.setdefault(vals[0], []).append(vals)
    return dict(b=b, atw=atw, ath=ath, start=start, recs=recs)

def main():
    path = sys.argv[1]
    f = load(path)
    b, atw, ath, start = f['b'], f['atw'], f['ath'], f['start']
    ink = [[int(b[start + y*atw + x] > 127) for x in range(atw)] for y in range(ath)]
    # connected components (4-connectivity)
    seen = [[False]*atw for _ in range(ath)]
    blobs = []
    for y in range(ath):
        for x in range(atw):
            if not ink[y][x] or seen[y][x]:
                continue
            stack = [(y, x)]
            seen[y][x] = True
            y0 = y1 = y; x0 = x1 = x
            n = 0
            while stack:
                cy, cx = stack.pop()
                n += 1
                y0 = min(y0, cy); y1 = max(y1, cy)
                x0 = min(x0, cx); x1 = max(x1, cx)
                for dy, dx in ((1,0),(-1,0),(0,1),(0,-1)):
                    ny, nx = cy+dy, cx+dx
                    if 0 <= ny < ath and 0 <= nx < atw and ink[ny][nx] and not seen[ny][nx]:
                        seen[ny][nx] = True
                        stack.append((ny, nx))
            blobs.append((y0, y1, x0, x1, n))
    blobs.sort(key=lambda t: (t[0], t[2]))
    print(f"{path}: {len(blobs)} ink blobs in {atw}x{ath}")
    # For each record (y/2, x/2): which blob contains it?
    for c in range(0x20, 0x7F):
        if c not in f['recs']:
            continue
        for vals in f['recs'][c]:
            y, x = vals[1]//2, vals[2]//2
            hit = None
            for (y0, y1, x0, x1, n) in blobs:
                if y0 <= y <= y1 and x0 <= x <= x1:
                    hit = (y0, y1, x0, x1, n)
                    break
            tag = f"blob({hit[0]}-{hit[1]},{hit[2]}-{hit[3]} n={hit[4]})" if hit else "no-blob"
            print(f"  {chr(c)!r} rec(f1={vals[1]},f2={vals[2]}) -> pix({y},{x}) {tag}")

if __name__ == '__main__':
    main()