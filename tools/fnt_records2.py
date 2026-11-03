#!/usr/bin/env python3
# fnt_records2.py - dump REAL 16-byte records for all ASCII chars + full metadata
# usage: python fnt_records2.py <file.fnt>
import struct, sys

def main():
    path = sys.argv[1]
    b = open(path, 'rb').read()
    cnt, hgt = struct.unpack_from('<HH', b, 0)
    nsect, magic, offSec, offBmp = struct.unpack_from('<IIII', b, 4)
    # per-char records start at rec0; find by scanning for the run-list end
    # Guess: records end at offSec, 16 bytes each, count = cnt
    recStart = offSec - cnt * 16
    print(f"{path}: cnt={cnt} hgt={hgt} recStart=0x{recStart:X} (runlist 0x100..0x{recStart-1:X})")

    print("\n== sorted char list 0x100..0x%X (u16, FFFF=terminator) ==" % recStart)
    lst = []
    o = 0x100
    while o + 1 < recStart:
        v = struct.unpack_from('<H', b, o)[0]
        if v == 0xFFFF:
            break
        lst.append(v)
        o += 2
    print(f"  {len(lst)} chars in list: " + ' '.join(f"{v:04X}" if not (32 <= v < 127) else chr(v) for v in lst[:200]))
    print("  total entries:", len(lst))

    print("\n== records (char @ recStart+(c-0x20)*16) ==")
    for ch in list(' !\"#$%&\'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~'):
        c = ord(ch)
        o = recStart + (c - 0x20) * 16
        if o + 16 > len(b):
            print(f"U+{c:04X} {ch!r}: out of range")
            continue
        vals = struct.unpack_from('<8H', b, o)
        y, x, w = vals[1], vals[2], vals[3]
        print(f"U+{c:04X} {ch!r}: @0x{o:X} fields={vals}  y={y} x={x} w={w}")

    print("\n== metadata region offBmp(0x%X) full hexdump (1080 bytes) ==" % offBmp)
    for r in range(offBmp, offBmp + 1080, 16):
        row = b[r:r+16]
        print(f"  {r:04X}: " + ' '.join(f'{x:02X}' for x in row))

if __name__ == '__main__':
    main()