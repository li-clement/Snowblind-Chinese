#!/usr/bin/env python3
# fnt_atlas.py - render .fnt glyph atlas to PNG + dump char slot fields + metadata
# usage: python fnt_atlas.py <file.fnt> <out.png> [--dump]
import struct, sys
from PIL import Image

def dump_hex(b, off, n, label):
    print(f"--- {label} @0x{off:X} ---")
    for r in range(off, min(off+n, len(b)), 16):
        row = b[r:r+16]
        hexs = ' '.join(f'{x:02X}' for x in row)
        print(f"  {r:04X}: {hexs}")
    print()

def main():
    path, out = sys.argv[1], sys.argv[2]
    b = open(path, 'rb').read()
    cnt, hgt = struct.unpack_from('<HH', b, 0)
    nsect, magic, offSec, offBmp = struct.unpack_from('<IIII', b, 4)
    atw, ath = struct.unpack_from('<HH', b, offBmp)
    print(f"{path}: cnt={cnt} hgt={hgt} nsect={nsect} offSec=0x{offSec:X} offBmp=0x{offBmp:X} atlas={atw}x{ath}")
    meta = 1080
    start = offBmp + meta
    need = atw * ath
    if start + need > len(b):
        print(f"atlas does not fit: start=0x{start:X} need={need} filelen={len(b)}")
        start = len(b) - need
        print(f"adjusted start=0x{start:X}")
    img = Image.new('L', (atw, ath))
    img.putdata(b[start:start+need])
    img.save(out)
    print(f"saved {out} ({atw}x{ath}), atlas bytes @0x{start:X}")

    if '--dump' in sys.argv:
        dump_hex(b, 0x100, 0x80, "char table start")
        dump_hex(b, offBmp, 0x40, "offBmp header")
        dump_hex(b, offBmp+4, 240, "metadata (u32s)")
        # char slots for some ASCII
        print("--- char slots (4 x u16) ---")
        for ch in [' ', '0', 'A', 'B', 'a', 'z', '!']:
            c = ord(ch)
            # find slot: appears at 0x100 + 4*something; search table for c
            found = None
            for o in range(0x100, offSec-7, 4):
                f = struct.unpack_from('<H', b, o)
                if f[0] == c:
                    s4 = struct.unpack_from('<HHHH', b, o)
                    found = (o, s4)
                    break
            if found:
                o, s4 = found
                print(f"  U+{c:04X} {ch!r} @0x{o:X}: fields={s4}")
            else:
                print(f"  U+{c:04X} {ch!r}: not found")

if __name__ == '__main__':
    main()