import struct
XBE = r"E:\Game\ps5\iso\[XBOX].Baldur's.Gate.Dark.Alliance.[USA]\default.xbe"
TEXT_VA, TEXT_RAW, TEXT_SIZE = 0x11000, 0x1000, 0xDC79C
b = open(XBE, 'rb').read()
text = b[TEXT_RAW:TEXT_RAW + TEXT_SIZE]

# search for the constants 0x214, 0xAE4, 0xB8C, 0x434, 0x1080 as 32-bit immediates in code
# common encodings: 81 C? xx xx xx xx (add/sub/cmp), 8D 8? xx xx xx xx (lea), 68 (push imm32),
# B8+ (mov eax,imm32), 05 (add eax,imm32), 2D (sub eax,imm32), 3D (cmp eax,imm32)
for val, nm in ((0x214, 'recOff'), (0xAE4, 'kernOff'), (0xB8C, 'bmpOff'), (0x434, 'metaSz'), (0x1080, 'bmpOff1080'), (0x200, '512'), (0x9E, '158')):
    imm = struct.pack('<I', val)
    hits = []
    pos = 0
    while True:
        i = text.find(imm, pos)
        if i < 0:
            break
        hits.append(TEXT_VA + i)
        pos = i + 1
    print('%s 0x%X: %d hits' % (nm, val, len(hits)))
    print('   ', [hex(h) for h in hits[:30]])