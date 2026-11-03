# find writers/readers of UV scale globals 0x25DD00/4 and how FSet sets them
import struct

XBE = r"E:\Game\ps5\iso\[XBOX].Baldur's.Gate.Dark.Alliance.[USA]\default.xbe"
b = open(XBE, 'rb').read()
text_raw = 0x1000
text_va = 0x11000
text_size = 0xDC79C
text = b[text_raw:text_raw + text_size]

for name, addr in (('UV_X', 0x25DD00), ('UV_Y', 0x25DD04), ('cnt?', 0x25DD08), ('curfont', 0x25DD18)):
    enc = struct.pack('<I', addr)
    hits = []
    start = 0
    while True:
        i = text.find(enc, start)
        if i < 0:
            break
        va = text_va + i
        pre = text[i-1] if i >= 1 else 0
        # dword loads: A1(mov eax), 8B 0D(ecx), 8B 15(edx), D9 05(fld m32), D9 1D(fstp m32), 89 05(mov [m],eax)
        kind = {0xA1: 'mov eax', 0x8B: 'mov r32', 0x89: 'mov [m],r32', 0xD9: 'fld/fstp m32', 0xC7: 'mov [m],imm'}.get(pre, f'0x{pre:02X}')
        hits.append((va, kind))
        start = i + 1
    print(f'{name} 0x{addr:X}: {len(hits)} refs')
    for h, k in hits[:30]:
        print(f'   0x{h:X} ({k})')
    print()