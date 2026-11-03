import struct
XBE = r"E:\Game\ps5\iso\[XBOX].Baldur's.Gate.Dark.Alliance.[USA]\default.xbe"
TEXT_VA, TEXT_RAW, TEXT_SIZE = 0x11000, 0x1000, 0xDC79C
b = open(XBE, 'rb').read()
text = b[TEXT_RAW:TEXT_RAW + TEXT_SIZE]

# find call targets == some VA (E8 rel32 or FF 15 / FF 25 / FF D0 etc.)
def calls_to(target):
    hits = []
    for i in range(len(text) - 5):
        if text[i] == 0xE8:
            rel = struct.unpack_from('<i', text, i + 1)[0]
            tgt = TEXT_VA + i + 5 + rel
            if tgt == target:
                hits.append((TEXT_VA + i, 'E8'))
        elif text[i] == 0xE9:
            rel = struct.unpack_from('<i', text, i + 1)[0]
            tgt = TEXT_VA + i + 5 + rel
            if tgt == target:
                hits.append((TEXT_VA + i, 'E9'))
    return hits

for tgt in (0x66D10, 0x7EFB0, 0x7F000, 0x654F0, 0x66A20, 0x66A90, 0x67580, 0x67608):
    hits = calls_to(tgt)
    print('callers of 0x%X: %s' % (tgt, ', '.join('0x%X(%s)' % (h, k) for h, k in hits) if hits else 'NONE'))