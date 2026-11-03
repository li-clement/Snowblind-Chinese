import sys
b = open(r"E:\Game\ps5\iso\[XBOX].Baldur's.Gate.Dark.Alliance.[USA]\default.xbe", 'rb').read()
for va in (0x1159C0, 0x115B70, 0x115FF0, 0x118950, 0x118990, 0x1189F0, 0x118200, 0x117F40, 0x1190B0):
    off = 0x1000 + (va - 0x11000)
    print(f'{va:#x} (file {off:#x}): {b[off:off+24].hex()}')