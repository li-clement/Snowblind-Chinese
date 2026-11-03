import struct
b = open(r"E:\Game\ps5\iso\[XBOX].Baldur's.Gate.Dark.Alliance.[USA]\default.xbe", 'rb').read()
TEXT_RAW, TEXT_VA, TEXT_SIZE = 0x1000, 0x11000, 0xDC79C
text = b[TEXT_RAW:TEXT_RAW+TEXT_SIZE]

def find_call_target(target):
    hits = []
    for i in range(len(text) - 5):
        if text[i] == 0xE8:
            rel = struct.unpack_from('<i', text, i+1)[0]
            va = TEXT_VA + i
            dest = (va + 5 + rel) & 0xFFFFFFFF
            if dest == target:
                hits.append(va)
    return hits

print('call 0x66D10 (FSet):', [hex(h) for h in find_call_target(0x66D10)])
# also check other font-related functions found earlier
for tgt in (0x66D10, 0x66F10, 0x67580, 0x654F0, 0x66A20, 0x66020):
    hits = find_call_target(tgt)
    if hits:
        print(f'call {tgt:#x}: {[hex(h) for h in hits]}')