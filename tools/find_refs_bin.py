import re
b = open(r"E:\Game\ps5\iso\[XBOX].Baldur's.Gate.Dark.Alliance.[USA]\default.xbe", 'rb').read()
TEXT_RAW, TEXT_VA = 0x1000, 0x11000
text = b[TEXT_RAW:TEXT_RAW + 0xDC79C]

# common encodings for [0x2803A8] = a8 03 28 00 ; [0x2803a0] = a0 03 28 00
for name, addr in [('2803A8', 'a8032800'), ('2803A0', 'a0032800'), ('2803A4', 'a4032800'), ('2803AC', 'ac032800'), ('27E150', '50e12700'), ('27E180', '80e12700'), ('27E18C', '8ce12700')]:
    pat = bytes.fromhex(addr)
    hits = [m.start() for m in re.finditer(re.escape(pat), text)]
    print(f'== bytes {addr} ({name}) ==')
    for h in hits:
        va = TEXT_VA + h
        # print 3 bytes before as opcode prefix hint
        print(f'  0x{va:06X}  (pre: {text[h-2:h].hex()})')