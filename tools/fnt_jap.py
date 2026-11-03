#!/usr/bin/env python3
# fnt_jap.py - verify record layout on japfontbig0: find chars, render glyphs, dump 0x100 list
import struct, sys

def main():
    path = sys.argv[1]
    b = open(path, 'rb').read()
    cnt, hgt = struct.unpack_from('<HH', b, 0)
    nsect, magic, offSec, offBmp = struct.unpack_from('<IIII', b, 4)
    atw, ath = struct.unpack_from('<HH', b, offBmp)
    start = offBmp + 1080
    recStart = offSec - cnt * 16
    print(f"{path}: cnt={cnt} hgt={hgt} nsect={nsect} offSec=0x{offSec:X} offBmp=0x{offBmp:X}")
    print(f"recStart=0x{recStart:X} atlas={atw}x{ath} atlasStart=0x{start:X}")

    # 1) dump 0x100..recStart as hex
    print(f"\n== 0x100..0x{recStart-1:X} (char list region, {recStart-0x100} bytes) ==")
    for r in range(0x100, recStart, 16):
        row = b[r:r+16]
        print(f"  {r:04X}: " + ' '.join(f'{x:02X}' for x in row))

    # 2) find records by fields[0]
    print("\n== records containing specific chars in field[0] ==")
    targets = [0x20, 0x41, 0x61, 0x3042, 0x30A2, 0x6F22, 0x4E00]
    for t in targets:
        found = None
        for i in range(cnt):
            o = recStart + i*16
            c0 = struct.unpack_from('<H', b, o)[0]
            if c0 == t:
                found = i
                break
        if found is None:
            print(f"U+{t:04X}: not found in records")
        else:
            o = recStart + found*16
            vals = struct.unpack_from('<8H', b, o)
            print(f"U+{t:04X}: glyph idx {found} @0x{o:X} fields={vals}")
            y, x = vals[1], vals[2]
            if y + hgt <= ath and x + atw <= atw:
                print(f"  render @({x},{y}):")
                for r in range(y, min(y + hgt + 2, ath)):
                    row = b[start + r*atw + x : start + r*atw + x + 32]
                    s = ''.join('#' if v > 127 else ('.' if v > 0 else ' ') for v in row)
                    print(f"   {r:03d}|{s}|")
                # full 24px-tall render using fields[1] as y
                y2 = vals[1]
                print(f"  full render y0={y2} h=x24:")
                for r in range(y2, min(y2 + 26, ath)):
                    row = b[start + r*atw + x : start + r*atw + x + 28]
                    s = ''.join('#' if v > 127 else ('.' if v > 0 else ' ') for v in row)
                    print(f"   {r:03d}|{s}|")

if __name__ == '__main__':
    main()