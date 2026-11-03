import struct
XBE = r"E:\Game\ps5\iso\[XBOX].Baldur's.Gate.Dark.Alliance.[USA]\default.xbe"
b = open(XBE,'rb').read()
TEXT_VA, TEXT_RAW, TEXT_SIZE = 0x11000, 0x1000, 0xDC79C
text = b[TEXT_RAW:TEXT_RAW+TEXT_SIZE]
# find writes to 0x233F44 / 48 / 4C: A3 (mov moffs32,eax) or 89 0D/15/1D ... 
for slot in (0x233F44, 0x233F48, 0x233F4C):
    print(f"== writes to 0x{slot:X} ==")
    # A3 xx xx xx xx = mov [imm32], eax
    pat = b'\xA3' + struct.pack('<I', slot)
    pos = 0
    while True:
        i = text.find(pat, pos)
        if i < 0: break
        print(f"  mov [slot], eax  @ 0x{TEXT_VA+i:06X}")
        pos = i+1
    # 89 0D xx xx xx xx = mov [imm32], ecx
    for reg in (0x0D, 0x15, 0x1D, 0x05):
        pat = b'\x89' + bytes([reg]) + struct.pack('<I', slot)
        pos = 0
        while True:
            i = text.find(pat, pos)
            if i < 0: break
            print(f"  mov [slot], r  @ 0x{TEXT_VA+i:06X}")
            pos = i+1
