import struct
b = open(r"E:\Game\ps5\iso\[XBOX].Baldur's.Gate.Dark.Alliance.[USA]\default.xbe", 'rb').read()

# XBE header: magic at 0, section count at 0x104 (size of certificate?), section headers at 0x118
ep = struct.unpack_from('<I', b, 0x104)[0]  # actually guessed; print header fields
sec_cnt = struct.unpack_from('<I', b, 0x108)[0]
print(f'ep={ep:#x} sec_cnt={sec_cnt}')
print('first bytes:', b[:32].hex())
# XBE format: 0x00 magic 'XBEH', 0x04 base, 0x08 size of headers
magic = b[0:4]
base = struct.unpack_from('<I', b, 4)[0]
hdr_size = struct.unpack_from('<I', b, 8)[0]
print(f'magic={magic} base={base:#x} hdr_size={hdr_size:#x}')
# section headers at base+0x1D4? standard: 0x118..0x118+0x14... let's just scan for section table at 0x118
# standard XBE layout:
#  0x104 DWORD size of certificate
#  0x108 DWORD number of sections
#  0x10C DWORD shared library crc
#  0x110 DWORD xboxkrnl image base?
#  0x114 DWORD entry point
#  0x118 DWORD base address
#  0x11C DWORD size of headers
#  ...
#  0x124 DWORD section headers VA
# ...
sect_va_ptr = struct.unpack_from('<I', b, 0x124)[0]
print(f'section headers VA ptr = {sect_va_ptr:#x}')
# section header entry: 24 bytes: VirtualAddress, VirtualSize, RawAddress, RawSize, SectionNamePtr, RefCount, SharedRefCount, SectionDigest, SectionPre...
# Actually XBOX XBE section entry = 40 bytes? Let's dump 0x118-0x160 raw
for i in range(0, 0x200, 0x20):
    print(f'{i:04x}: ' + b[i:i+32].hex())