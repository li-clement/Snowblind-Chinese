# scan E8 call sites, resolve rel32, find calls to target functions
import struct

XBE = r"E:\Game\ps5\iso\[XBOX].Baldur's.Gate.Dark.Alliance.[USA]\default.xbe"
b = open(XBE, 'rb').read()
text_raw = 0x1000
text_va = 0x11000
text_size = 0xDC79C
text = b[text_raw:text_raw + text_size]

targets = {
    0x668D0: 'SetCurrentFont',
    0x66A90: 'TranslateWrap',
    0x67580: 'DrawChars',
    0x66A20: 'TranslateString',
    0x66D10: 'FSet',
}

# build map of all E8 destinations
calls = {}
i = 0
while i < len(text):
    if text[i] == 0xE8 and i + 4 < len(text):
        rel = struct.unpack_from('<i', text, i + 1)[0]
        site = text_va + i
        dest = site + 5 + rel
        calls.setdefault(dest, []).append(site)
        i += 5
    else:
        i += 1

for tgt, name in targets.items():
    sites = calls.get(tgt, [])
    print(f'{name} 0x{tgt:X}: {len(sites)} E8 callers')
    for h in sites[:50]:
        print(f'   0x{h:X}')
    print()