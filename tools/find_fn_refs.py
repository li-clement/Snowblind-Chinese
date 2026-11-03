# search for 4-byte absolute refs to key font functions (indirect call targets)
import struct

XBE = r"E:\Game\ps5\iso\[XBOX].Baldur's.Gate.Dark.Alliance.[USA]\default.xbe"
b = open(XBE, 'rb').read()
text_raw = 0x1000
text_va = 0x11000
text_size = 0xDC79C
text = b[text_raw:text_raw + text_size]

for name, addr in (('TranslateString', 0x66A20), ('FSet', 0x66D10), ('DrawChars', 0x67580),
                   ('UniParsed? 0x66A90', 0x66A90), ('render 0x67980', 0x67980)):
    enc = struct.pack('<I', addr)
    hits = []
    start = 0
    while True:
        i = text.find(enc, start)
        if i < 0:
            break
        va = text_va + i
        hits.append(va)
        start = i + 1
    print(f'{name} 0x{addr:X}: {len(hits)} imm refs')
    for h in hits[:25]:
        print(f'   0x{h:X}')