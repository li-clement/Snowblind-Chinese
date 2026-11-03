#!/usr/bin/env python3
# fnt_records.py - dump full 16-byte records for chars + metadata region
# usage: python fnt_records.py <file.fnt>
import struct, sys

def main():
    path = sys.argv[1]
    b = open(path, 'rb').read()
    cnt, hgt = struct.unpack_from('<HH', b, 0)
    nsect, magic, offSec, offBmp = struct.unpack_from('<IIII', b, 4)
    print(f"{path}: cnt={cnt} hgt={hgt} nsect={nsect} offSec=0x{offSec:X} offBmp=0x{offBmp:X}")
    print(f"table bytes 0x100..0x{offSec:X} = {offSec-0x100}")

    # Find record start for a char: records start at 0x100? try offsets 0x100+k*8
    # First locate 'A' (0x41) by scanning 4-byte steps for u16==0x41
    def find_rec(ch, step, ms):
        c = ord(ch)
        hits = []
        for o in range(0x100, offSec - ms, step):
            if struct.unpack_from('<H', b, o)[0] == c:
                hits.append(o)
        return hits

    print("\n== record starts (first u16 == char): step=16 (8 u16s), 20 bytes shown ==")
    for ch in list('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 .,;:!?()[]-+\'\"*/') :
        hits = find_rec(ch, 16, 20)
        if hits:
            o = hits[0]
            vals = struct.unpack_from('<10H', b, o)
            print(f"U+{ord(ch):04X} {ch!r} @0x{o:X}: {vals}  (+0x{o-0x100:X})")
        else:
            print(f"U+{ord(ch):04X} {ch!r}: <none at 16-step>")

    print("\n== raw hex 0x100..0x260 ==")
    for r in range(0x100, 0x260, 16):
        row = b[r:r+16]
        print(f"  {r:04X}: " + ' '.join(f'{x:02X}' for x in row))

    print("\n== metadata region 0x%X .. 0x%X (hex) ==" % (offBmp, offBmp+176))
    for r in range(offBmp, offBmp+176, 16):
        row = b[r:r+16]
        print(f"  {r:04X}: " + ' '.join(f'{x:02X}' for x in row))

if __name__ == '__main__':
    main()