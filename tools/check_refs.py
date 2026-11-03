import re
b = open(r"E:\Game\ps5\iso\[XBOX].Baldur's.Gate.Dark.Alliance.[USA]\default.xbe", 'rb').read()
TEXT_RAW, TEXT_VA, TEXT_SIZE = 0x1000, 0x11000, 0xDC79C
text = b[TEXT_RAW:TEXT_RAW+TEXT_SIZE]

# 1) does the US XBE reference jap font names at all?
for s in [b'japfontbig0', b'japfontsmall0', b'gamefonta', b'gamefontmed', b'gamefontsmall', b'bigfont', b'creditfont']:
    hits = [m.start() for m in re.finditer(re.escape(s), text)]
    print(f'{s.decode()}: {len(hits)} refs')
    for h in hits[:3]:
        # decode the string at that spot
        seg = text[h-8:h+40]
        print(f'   @ {TEXT_VA+h:#x}: {seg[:48]!r}')

# 2) callers of 0x5F3D8 (font.lmp loader)
def find_call_target(target):
    hits = []
    import struct
    for i in range(len(text) - 5):
        if text[i] == 0xE8:
            rel = struct.unpack_from('<i', text, i+1)[0]
            va = TEXT_VA + i
            dest = (va + 5 + rel) & 0xFFFFFFFF
            if dest == target:
                hits.append(va)
    return hits
print('callers of 0x5F3D8 (font.lmp load):', [hex(h) for h in find_call_target(0x5F3D8)])