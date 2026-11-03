import struct
XBE = "E:\\Game\\ps5\\iso\\[XBOX].Baldur's.Gate.Dark.Alliance.[USA]\\default.xbe"
b = open(XBE, 'rb').read()
TEXT_VA, TEXT_RAW, TEXT_SIZE = 0x11000, 0x1000, 0xDC79C
text = b[TEXT_RAW:TEXT_RAW + TEXT_SIZE]

for slot in (0x233f44, 0x233f48, 0x233f4c, 0x233f40, 0x233f0c):
    imm = struct.pack('<I', slot)
    print('== refs to 0x%X ==' % slot)
    pos = 0
    while True:
        i = text.find(imm, pos)
        if i < 0:
            break
        print('  0x%06X (file 0x%X)' % (TEXT_VA + i, TEXT_RAW + i))
        pos = i + 1