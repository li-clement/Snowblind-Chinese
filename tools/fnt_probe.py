#!/usr/bin/env python3
# fnt_probe.py - probe Snowblind .fnt: mapping table, section table, glyph records
# usage: python fnt_probe.py <file.fnt>
import struct, sys

def art(bits, w, h, label):
    if len(bits) < w * h:
        return
    print(f"--- {label} ({w}x{h}) ---")
    for y in range(h):
        row = bits[y*w:(y+1)*w]
        print(''.join('#' if v > 127 else ('.' if v > 0 else ' ') for v in row))
    print()

def main(path):
    b = open(path, 'rb').read()
    cnt, hgt = struct.unpack_from('<HH', b, 0)
    nsect, magic, offSec, offBmp = struct.unpack_from('<IIII', b, 4)
    print(f"{path} size={len(b)} cnt={cnt} hgt={hgt} nsect={nsect} magic={magic} offSec=0x{offSec:X} offBmp=0x{offBmp:X}")

    # ---- 1) mapping table at 0x100 ----
    pairs = {}
    o = 0x100
    while o + 3 < offSec:
        c, g = struct.unpack_from('<HH', b, o)
        pairs.setdefault(c, []).append((g, o))
        o += 4
    print(f"mapping table: {len(pairs)} distinct charCodes in {o-0x100} bytes at 0x100..0x{offSec:X}")
    for ch in ['A','B','C','D','a','b','0','1','5',' ','!','.',',','\u4e00','\u4f60','\u597d']:
        c = ord(ch)
        if c in pairs:
            gl = pairs[c]
            print(f"  U+{c:04X} {ch!r}: {len(gl)} entries {[x[0] for x in gl[:4]]} @" +
                  ','.join(f"0x{x[1]:X}" for x in gl[:4]))
        else:
            print(f"  U+{c:04X} {ch!r}: NOT in table")

    # ---- 2) section table ----
    print(f"--- section table @0x{offSec:X} ({nsect} recs x 6 bytes) ---")
    for i in range(nsect):
        a, b2, c2 = struct.unpack_from('<HHh', b, offSec + i*6)
        print(f"  sec[{i}]: start=U+{a:04X} count={b2} glyphBase={c2}")
    print()

    # ---- 3) glyph data: try per-glyph record layout ----
    print(f"--- glyph data @0x{offBmp:X} ---")
    dump16(b, offBmp, 0x60, "offBmp header")
    # guess: after a small subheader, records of (u16 w,u16 h,u16 xoff,u16 yoff) + w*h bytes
    # scan a few positions and render art to find letters
    p = offBmp
    for head_try in range(6):
        w, hh, xo, yo = struct.unpack_from('<HHhh', b, p + head_try*16) if head_try < 2 else (0,0,0,0)
    # Direct: try treating offBmp as start of records; print first 6 raw records
    for k in range(8):
        rp = offBmp + 8 + k*16
        if rp + 16 > len(b): break
        w, hh, xo, yo = struct.unpack_from('<HHhh', b, rp)
        print(f"  rec@{rp:#x}: w={w} h={hh} xo={xo} yo={yo}")
        if 4 <= w <= 64 and 4 <= hh <= 48 and rp + 16 + w*hh <= len(b):
            art(b[rp+16:rp+16+w*hh], w, hh, f"rec@{rp:#x}")

def dump16(b, off, n, label):
    print(f"--- {label} @0x{off:X} ---")
    for r in range(off, min(off+n, len(b)), 16):
        row = b[r:r+16]
        hexs = ' '.join(f'{x:02X}' for x in row)
        asc = ''.join(chr(x) if 32 <= x < 127 else '.' for x in row)
        print(f"  {r:04X}: {hexs:<47} {asc}")
    print()

if __name__ == '__main__':
    main(sys.argv[1])