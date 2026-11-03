#!/usr/bin/env python3
# fnt_slots.py - verify char slot (y,x) hypothesis by rendering glyphs from atlas
# usage: python fnt_slots.py <file.fnt> [chars...]
import struct, sys

def main():
    path = sys.argv[1]
    chars = list(sys.argv[2]) if len(sys.argv) > 2 else list('ABCZ01!abc.,;: ')
    b = open(path, 'rb').read()
    cnt, hgt = struct.unpack_from('<HH', b, 0)
    nsect, magic, offSec, offBmp = struct.unpack_from('<IIII', b, 4)
    atw, ath = struct.unpack_from('<HH', b, offBmp)
    start = offBmp + 1080

    # build slot map: first 4-byte slot whose first u16 == char
    slots = {}
    for o in range(0x100, offSec-7, 4):
        c = struct.unpack_from('<H', b, o)[0]
        if c not in slots:
            slots[c] = struct.unpack_from('<HHHH', b, o)
    print(f"slots parsed: {len(slots)} unique chars (cnt field={cnt})")

    for ch in chars:
        c = ord(ch)
        if c not in slots:
            print(f"U+{c:04X} {ch!r}: NO SLOT")
            continue
        f = slots[c]
        y, x = f[1], f[2]
        print(f"U+{c:04X} {ch!r}: fields={f}")
        if y + hgt > ath or x + 64 > atw:
            print("   (out of atlas bounds)")
            continue
        for r in range(y, y + hgt):
            row = b[start + r*atw + x : start + r*atw + x + 32]
            s = ''.join('#' if v > 127 else ('.' if v > 0 else ' ') for v in row)
            print(f"   {r:03d}|{s}|")
        print()

if __name__ == '__main__':
    main()