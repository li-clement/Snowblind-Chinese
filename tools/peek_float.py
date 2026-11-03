import struct
b = open(r"E:\Game\ps5\iso\[XBOX].Baldur's.Gate.Dark.Alliance.[USA]\default.xbe", 'rb').read()
# .rdata VA=0x1385A0 file=0x127000
def rd(va):
    f = 0x127000 + (va - 0x1385A0)
    return b[f]
for va in (0x1388B8,):
    f = 0x127000 + (va - 0x1385A0)
    raw = b[f:f+8]
    print(f'VA {va:#x} file {f:#x}: raw={raw.hex()} f32le={struct.unpack_from("<f", raw, 0)[0]!r} u32={struct.unpack_from("<I", raw, 0)[0]:#x}')
    print(f'  +4: f32le={struct.unpack_from("<f", raw, 4)[0]!r} u32={struct.unpack_from("<I", raw, 4)[0]:#x}')
# also dump floats around 0x1388B8 to find neighbors
print('floats around 1388B8:')
for i in range(-4, 5):
    f = 0x127000 + (0x1388B8 - 0x1385A0) + i*4
    print(f'  {0x1388B8+i*4:#x}: {struct.unpack_from("<f", b, f)[0]!r}')