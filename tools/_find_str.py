import struct
XBE = "E:\\Game\\ps5\\iso\\[XBOX].Baldur's.Gate.Dark.Alliance.[USA]\\default.xbe"
b = open(XBE, 'rb').read()
TEXT_VA, TEXT_RAW, TEXT_SIZE = 0x11000, 0x1000, 0xDC79C
text = b[TEXT_RAW:TEXT_RAW + TEXT_SIZE]

strings = {
    0x13ED98: 'font.lmp', 0x13ED88: 'gamefonta.fnt', 0x13ED78: 'gamefontmed.fnt',
    0x13ED64: 'gamefontsmall.fnt', 0x13ED58: 'gtext.lmp',
    0x14038C: 'frontend.lmp', 0x140520: 'creditfont.fnt', 0x140550: 'bigfont.fnt',
    0x13E858: 'str_13e858', 0x13E84C: 'str_13e84c', 0x13ECC0: 'str_13ecc0',
    0x13ECCC: 'str_13eccc', 0x13ED4C: 'str_13ed4c', 0x13ED40: 'str_13ed40',
}
for va, nm in sorted(strings.items()):
    imm = struct.pack('<I', va)
    print('== refs to %s (0x%X) ==' % (nm, va))
    pos = 0
    cnt = 0
    while True:
        i = text.find(imm, pos)
        if i < 0:
            break
        print('  0x%06X' % (TEXT_VA + i))
        cnt += 1
        pos = i + 1
    if cnt == 0:
        print('  (none)')