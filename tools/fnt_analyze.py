#!/usr/bin/env python3
# fnt_analyze.py - deep analysis of Snowblind .fnt bitmap font format
# usage: python fnt_analyze.py <file.fnt> [more.fnt ...]
import struct, sys, os

def hexdump(b, off, n, label=""):
    print(f"--- {label} @0x{off:X} (first {n} bytes) ---")
    end = min(off + n, len(b))
    for r in range(off, end, 16):
        row = b[r:r+16]
        hexs = ' '.join(f'{x:02X}' for x in row)
        asc = ''.join(chr(x) if 32 <= x < 127 else '.' for x in row)
        print(f"  {r:04X}: {hexs:<47} {asc}")
    print()

def analyze(path):
    b = open(path, 'rb').read()
    cnt, h = struct.unpack_from('<HH', b, 0)
    s4, s8, off12, off16 = struct.unpack_from('<IIII', b, 4)
    print(f"===== {os.path.basename(path)}  size={len(b)} =====")
    print(f"u16[0]={cnt} u16[2]={h} u32[4]={s4} u32[8]={s8} u32[12]=0x{off12:X} u32[16]=0x{off16:X}")
    hexdump(b, 0, 0x40, "header")
    # count valid pairs in the (charCode,glyphIdx) table starting at 0x100
    valid = 0
    firsts = []
    lo = 0x100
    hi = min(off12, len(b))
    for o in range(lo, hi-3, 4):
        c, idx = struct.unpack_from('<HH', b, o)
        if c != 0xFFFF or idx != 0xFFFF:
            valid += 1
            if len(firsts) < 16:
                firsts.append((o, c, idx))
    print(f"valid (char->glyph) pairs from 0x100 to 0x{hi:X}: {valid}")
    for o, c, idx in firsts:
        if 32 <= c < 128:
            print(f"  @0x{o:04X}  U+{c:04X} ({chr(c)}) -> glyph {idx}")
        else:
            print(f"  @0x{o:04X}  U+{c:04X} -> glyph {idx}")
    # What is between the table end and off12? try to detect table length = cnt?
    if valid == cnt:
        print(f"  -> pair count == u16[0] ({cnt}): table size {cnt*4} bytes, ends 0x{0x100+cnt*4:X}")
    hexdump(b, off12, 0x80, "off12 region")
    hexdump(b, off16, 0x80, "off16 region")
    # byte histogram in the tail data area (after off12) to tell 1bpp vs 8bpp
    from collections import Counter
    tail = b[max(off12, off16):]
    cnts = Counter(tail)
    top = cnts.most_common(8)
    print(f"tail histogram (top {len(top)}): " + ", ".join(f"0x{x:02X}:{n}" for x, n in top))
    # count distinct byte values in tail
    print(f"tail distinct byte values: {len(cnts)}  (2 -> 1bpp; many -> antialiased/8bpp)")
    # check for a monospaced stride: if 1bpp and width = height, stride = ceil(w/8)
    print()

for p in sys.argv[1:]:
    analyze(p)