# find refs to current-font global 0x25DD18
import struct

XBE = r"E:\Game\ps5\iso\[XBOX].Baldur's.Gate.Dark.Alliance.[USA]\default.xbe"
b = open(XBE, 'rb').read()
text_raw = 0x1000
text_va = 0x11000
text_size = 0xDC79C
text = b[text_raw:text_raw + text_size]

addr = 0x25DD18
enc = struct.pack('<I', addr)
hits = []
start = 0
while True:
    i = text.find(enc, start)
    if i < 0:
        break
    va = text_va + i
    # byte before: A1=mov eax,[m] ; 89 05=mov [m],eax ; 8B 0D=mov ecx,[m] ; C7 05=mov dword[m],imm ; 3B 05 cmp eax,[m]
    pre = text[i-1] if i >= 1 else 0
    kind = {0xA1: 'mov eax,[m]', 0x8B: 'mov r32,[m]', 0x89: 'mov [m],r32', 0xC7: 'mov [m],imm32', 0x3B: 'cmp r32,[m]'}.get(pre, f'pre=0x{pre:02X}')
    print(f'0x{va:X}  ({kind})')
    hits.append(va)
    start = i + 1
print('total', len(hits))