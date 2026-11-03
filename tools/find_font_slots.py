# find references to font globals 0x233F44/a/48/med/4C/small and render callers
import subprocess, re, struct, os

XBE = r"E:\Game\ps5\iso\[XBOX].Baldur's.Gate.Dark.Alliance.[USA]\default.xbe"
b = open(XBE, 'rb').read()

# .text sections: find from headers quickly (raw 0x1000, VA 0x11000, size 0xDC79C)
text_raw = 0x1000
text_va = 0x11000
text_size = 0xDC79C
text = b[text_raw:text_raw + text_size]

targets = {0x233F44: 'gamefonta', 0x233F48: 'gamefontmed', 0x233F4C: 'gamefontsmall'}

results = {}
for addr, name in targets.items():
    enc = struct.pack('<I', addr)
    hits = []
    start = 0
    while True:
        i = text.find(enc, start)
        if i < 0:
            break
        va = text_va + i
        # classify: mov eax,[addr] = A1 xx xx xx xx ; mov [..], eax ; lea eax,[addr] = 8D 05; cmp
        hits.append(va)
        start = i + 1
    results[name] = hits
    print(f'{name} 0x{addr:X}: {len(hits)} refs')
    for h in hits[:40]:
        print(f'  0x{h:X}')
print()
# also look for 0x66a20 callers (TranslateString) and 0x66d10 FSet callers
for fn, fnaddr in (('TranslateString', 0x66A20), ('FSet', 0x66D10), ('0x67580 drawchar', 0x67580)):
    enc = struct.pack('<I', fnaddr)
    hits = []
    start = 0
    while True:
        i = text.find(enc, start)
        if i < 0:
            break
        va = text_va + i
        # check preceding byte is E8 (call rel32)
        if i >= 1 and text[i - 1] == 0xE8:
            hits.append(va - 5)
        # also check 0x66D10 - maybe called via register
        start = i + 1
    print(f'{fn} 0x{fnaddr:X}: {len(hits)} direct callers')
    for h in hits[:30]:
        print(f'  0x{h:X}')