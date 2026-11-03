import struct
XBE = r"E:\Game\ps5\iso\[XBOX].Baldur's.Gate.Dark.Alliance.[USA]\default.xbe"
b = open(XBE, 'rb').read()
# XBE header: magic 'XBEH' at 0, size 0x100
print('magic:', b[:4])
# BaseAddress at offset 0x104
base, = struct.unpack_from('<I', b, 0x104)
print('BaseAddress: 0x%X' % base)
# SizeOfHeaders
soh, = struct.unpack_from('<I', b, 0x108)
print('SizeOfHeaders: 0x%X' % soh)
# section count at 0x10C?
nsec, = struct.unpack_from('<I', b, 0x10C)
print('SectionCount: %d' % nsec)
# section headers start at 0x110, each 0x28 bytes? XBE section: 24 bytes: VirtualAddress, VirtualSize, RawAddress, RawSize, SectionName(8), then flags(4), then...
for i in range(nsec):
    off = 0x110 + i * 0x28
    va, vs, raw, rsize, name, flags = struct.unpack_from('<IIII8sI', b, off)
    # peek more
    print('sec%d: VA=0x%X vsize=0x%X raw=0x%X rs=0x%X name=%r' % (i, va, vs, raw, rsize, name))