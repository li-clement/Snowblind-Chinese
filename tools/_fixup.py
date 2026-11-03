import struct
XBE = r"E:\Game\ps5\iso\[XBOX].Baldur's.Gate.Dark.Alliance.[USA]\default.xbe"
TEXT_VA, TEXT_RAW, TEXT_SIZE = 0x11000, 0x1000, 0xDC79C
b = open(XBE, 'rb').read()
text = b[TEXT_RAW:TEXT_RAW + TEXT_SIZE]

# patterns for offset->pointer fixup:
# mov edx,[eax+8]; add edx,eax; mov [eax+8],edx   => 8B 50 08 03 D0 89 50 08
# mov ecx,[eax+8]; add ecx,eax; mov [eax+8],ecx   => 8B 48 08 03 C8 89 48 08
# lea edx,[eax+ecx] style
pats = {
    'mov edx,[eax+8];add edx,eax;mov[eax+8],edx': bytes.fromhex('8B500803D0895008'),
    'mov edx,[eax+C];add edx,eax;mov[eax+C],edx': bytes.fromhex('8B501003D0895010'),
    'mov ecx,[eax+8];add ecx,eax;mov[eax+8],ecx': bytes.fromhex('8B480803C8894808'),
    'mov ecx,[eax+10];add ecx,eax;mov[eax+10],ecx': bytes.fromhex('8B481003C8894810'),
    'add eax,8B8 pattern?': None,
}
for name, pat in pats.items():
    if pat is None:
        continue
    pos = 0
    hits = []
    while True:
        i = text.find(pat, pos)
        if i < 0:
            break
        hits.append(TEXT_VA + i)
        pos = i + 1
    print('%s: %d hits %s' % (name, len(hits), [hex(h) for h in hits[:20]]))

# another: mov eax,[slot]; mov edx,[eax+8]; lea edx,[edx+eax]; mov [eax+8],edx (lea variant)
# 8B 40 08 8D 14 02 89 50 08
pats2 = {
    'lea edx,[eax+edx] fixup +8': bytes.fromhex('8D1402895008'),
    'lea ecx,[eax+ecx] fixup +8': bytes.fromhex('8D0C08894808'),
    'lea edx,[edx+eax] then +C/+10': bytes.fromhex('8D140289500C'),
    'lea edx,[edx+eax] then +10': bytes.fromhex('8D1402895010'),
}
for name, pat in pats2.items():
    pos = 0
    hits = []
    while True:
        i = text.find(pat, pos)
        if i < 0:
            break
        hits.append(TEXT_VA + i)
        pos = i + 1
    print('%s: %d hits %s' % (name, len(hits), [hex(h) for h in hits[:20]]))