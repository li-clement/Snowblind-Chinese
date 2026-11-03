#!/usr/bin/env python3
# xbe_fontrefs2.py - indirect string-table xrefs + D3D import table
import struct, re, sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

XBE = r"E:\Game\ps5\iso\[XBOX].Baldur's.Gate.Dark.Alliance.[USA]\default.xbe"
TEXT_VA, TEXT_RAW, TEXT_SIZE = 0x11000, 0x1000, 0xDC79C
RDATA_VA, RDATA_RAW, RDATA_SIZE = 0x1385A0, 0x127000, 0x18498

b = open(XBE, 'rb').read()
text = b[TEXT_RAW:TEXT_RAW + TEXT_SIZE]
rdata = b[RDATA_RAW:RDATA_RAW + RDATA_SIZE]

font_files = {
    0x13D7C4: 'gamefontsmall.fnt', 0x13D7D8: 'gamefontmed.fnt',
    0x13D7E8: 'gamefonta.fnt', 0x13D7F8: 'font.lmp',
    0x13EF80: 'creditfont.fnt', 0x13EFB0: 'bigfont.fnt',
    0x13EDEC: 'frontend.lmp',
}
# 1) find pointer tables in rdata pointing at these strings
print("== rdata strings as pointer targets ==")
ptrtable = {}
for off in range(0, len(rdata) - 3, 4):
    v = struct.unpack_from('<I', rdata, off)[0]
    if v in font_files:
        ptrtable.setdefault(RDATA_VA + off, []).append(font_files[v])
for va in sorted(ptrtable):
    print(f"  rdata ptr @0x{va:X}: {', '.join(ptrtable[va])}")

# 2) dump rdata region around the font strings to see the string table layout
print("\n== rdata around 0x13D780..0x13D810 ==")
off = 0x13D780 - RDATA_VA + RDATA_RAW
for i in range(off, off + 0x90, 16):
    row = rdata[i:i+16]
    hexs = ' '.join(f'{x:02X}' for x in row)
    asc = ''.join(chr(x) if 32 <= x < 127 else '.' for x in row)
    print(f"  {(RDATA_VA + i - RDATA_RAW):04X}: {hexs:<47} {asc}")

# 3) find refs in text to the pointer-table locations
targets = list(ptrtable.keys())
print("\n== text refs to rdata pointer-table addrs ==")
for off in range(0, len(text) - 3):
    v = struct.unpack_from('<I', text, off)[0]
    if v in targets:
        print(f"  0x{TEXT_VA + off:X}: ref 0x{v:X} -> {ptrtable[v]}")

# 4) import tables: read header fields
def u32(o): return struct.unpack_from('<I', b, o)[0]
entry = u32(0x12C)
kthunk = u32(0x158)
nkimport = u32(0x15C)
nlibs = u32(0x160)
libs = u32(0x164)
print(f"\n== header: entry=0x{entry:X} kthunk=0x{kthunk:X} nkimport=0x{nkimport:X} nlibs={nlibs} libs=0x{libs:X}")
# non-kernel import directory: list of IMAGE_IMPORT_DESCRIPTOR-ish
if nkimport:
    p = nkimport - 0x10000
    print("== non-kernel imports ==")
    for i in range(40):
        base = p + i * 20
        og = u32(base + 0)   # OriginalFirstThunk
        td = u32(base + 4)   # TimeDateStamp
        fwd = u32(base + 8)  # ForwarderChain
        name = u32(base + 12)
        ft = u32(base + 16)  # FirstThunk
        if name == 0 and og == 0 and ft == 0:
            break
        nf = name - 0x10000
        dll = b[nf:b.find(b'\x00', nf)].decode('ascii', 'replace')
        print(f"  imp[{i}]: dll={dll} OGT=0x{og:X} FT=0x{ft:X}")
        # list imported function names via OGT (or FT) array of IMAGE_THUNK_DATA
        th = og if og else ft
        thf = th - 0x10000
        names = []
        j = 0
        while j < 600:
            tv = u32(thf + j * 4)
            if tv == 0:
                break
            if tv & 0x80000000:
                names.append(f"ordinal:{tv & 0xFFFF}")
            else:
                pn = (tv & 0x7FFFFFFF) - 0x10000
                # IMAGE_IMPORT_BY_NAME: hint u16 + name
                nm = b[pn + 2:b.find(b'\x00', pn + 2)].decode('ascii', 'replace')
                names.append(nm)
            j += 1
        if names:
            print(f"     funcs({len(names)}): {', '.join(names[:80])}")