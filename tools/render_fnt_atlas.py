#!/usr/bin/env python3
# render_fnt_atlas.py <fnt> <out.png> [--grid] - visualize font atlas
import struct, sys
from PIL import Image

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
    return b, atw, ath, start, recs, cnt

def main():
    path, out = sys.argv[1], sys.argv[2]
    b, atw, ath, start, recs, cnt = load(path)
    scale = 4
    img = Image.new('RGB', (atw * scale, ath * scale), (30, 30, 30))
    px = img.load()
    atlastart = start
    for yy in range(ath):
        row = b[atlastart + yy * atw: atlastart + yy * atw + atw]
        for xx in range(atw):
            if row[xx] > 127:
                for dy in range(scale):
                    for dx in range(scale):
                        px[xx * scale + dx, yy * scale + dy] = (255, 255, 255)
    # draw record boxes (half-pixel coords -> /2)
    import math
    for c, v in recs.items():
        y0 = v[1] // 2
        x0 = v[2] // 2
        hh = max(1, (v[4] - v[3]) // 2)
        ww = max(1, v[6] // 2)
        color = (0, 200, 255) if 32 <= c < 127 else (255, 200, 0)
        for dy in range(scale):
            px[x0 * scale, (y0 + dy) * scale] = color
            px[(x0 + max(1, ww) - 1) * scale, (y0 + dy) * scale] = color
        for dx in range(max(1, ww) * scale):
            px[(x0 * scale) + dx, y0 * scale] = color
            px[(x0 * scale) + dx, (y0 + max(1, hh) - 1) * scale] = color
    img.save(out)
    print(f"atlas {atw}x{ath} cnt={cnt} -> {out}")

main()