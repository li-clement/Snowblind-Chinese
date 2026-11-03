# find E8 callers of SetCurrentFont 0x668D0, and of 0x66A90/0x66D10/0x67580 via E8 too
import struct

XBE = r"E:\Game\ps5\iso\[XBOX].Baldur's.Gate.Dark.Alliance.[USA]\default.xbe"
b = open(XBE, 'rb').read()
text_raw = 0x1000
text_va = 0x11000
text_size = 0xDC79C
text = b[text_raw:text_raw + text_size]

def find_callers(target):
    enc = struct.pack('<I', target)
    hits = []
    start = 0
    while True:
        i = text.find(enc, start)
        if i < 0:
            break
        rel = struct.unpack_from('<i', text, i)[0]
        site = text_va + i - 5          # E8 rel32: rel at i, instr at i-5
        # verify byte at i-5 is E8 (call)
        if i >= 5 and text[i-5] == 0xE8:
            dest = site + 5 + rel
            if dest == target:
                hits.append(site)
        start = i + 1
    return hits

for name, tgt in (('SetCurrentFont 0x668D0', 0x668D0), ('TranslateWrap 0x66A90', 0x66A90),
                  ('DrawChars 0x67580', 0x67580), ('FSet 0x66D10', 0x66D10)):
    hits = find_callers(tgt)
    print(f'{name}: {len(hits)} E8 callers')
    for h in hits[:40]:
        print(f'   0x{h:X}')
    print()