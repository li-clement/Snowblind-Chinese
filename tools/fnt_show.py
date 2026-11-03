#!/usr/bin/env python3
# fnt_show.py - render .fnt atlas region as ASCII art + hexdump metadata
# usage: python fnt_show.py <file.fnt> [y0] [y1] [x0] [x1]
import struct, sys

def main():
    path = sys.argv[1]
    y0 = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    y1 = int(sys.argv[3]) if len(sys.argv) > 3 else y0 + 12
    x0 = int(sys.argv[4]) if len(sys.argv) > 4 else 0
    x1 = int(sys.argv[5]) if len(sys.argv) > 5 else 256
    b = open(path, 'rb').read()
    cnt, hgt = struct.unpack_from('<HH', b, 0)
    nsect, magic, offSec, offBmp = struct.unpack_from('<IIII', b, 4)
    atw, ath = struct.unpack_from('<HH', b, offBmp)
    start = offBmp + 1080
    print(f"{path}: cnt={cnt} hgt={hgt} atlas={atw}x{ath} atlasStart=0x{start:X}")
    print(f"== atlas rows {y0}..{y1-1}, cols {x0}..{x1-1} ==")
    for y in range(y0, min(y1, ath)):
        row = b[start + y*atw + x0 : start + y*atw + x1]
        s = ''.join('#' if v > 127 else ('.' if v > 0 else ' ') for v in row)
        print(f"{y:03d}|{s}|")
    print()
    print("== offBmp area raw hex 0x%X..0x%X ==" % (offBmp, offBmp+0x80))
    for r in range(offBmp, min(offBmp+0x80, len(b)), 16):
        row = b[r:r+16]
        print(f"  {r:04X}: " + ' '.join(f'{x:02X}' for x in row))

if __name__ == '__main__':
    main()