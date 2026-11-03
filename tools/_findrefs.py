import struct
XBE = r"E:\Game\ps5\iso\[XBOX].Baldur's.Gate.Dark.Alliance.[USA]\default.xbe"
b = open(XBE,'rb').read()
TEXT_VA, TEXT_RAW, TEXT_SIZE = 0x11000, 0x1000, 0xDC79C
text = b[TEXT_RAW:TEXT_RAW+TEXT_SIZE]
font_strings = {
    0x13ED98: 'font.lmp', 0x13ED88: 'gamefonta.fnt', 0x13ED78: 'gamefontmed.fnt',
    0x13ED64: 'gamefontsmall.fnt', 0x13ED58: 'gtext.lmp',
    0x14038C: 'frontend.lmp', 0x140520: 'creditfont.fnt', 0x140550: 'bigfont.fnt',
    0x13e858: 'str_13e858', 0x13e84c: 'str_13e84c',
}
print("== refs to font strings in .text (push imm32 / mov r,imm32) ==")
for va, nm in sorted(font_strings.items()):
    imm = struct.pack('<I', va)
    for prefix in (b'\x68', b'\xB8', b'\xB9', b'\xBA', b'\xBB', b'\xBC', b'\xBD', b'\xBE', b'\xBF'):
        pat = prefix + imm
        pos = 0
        while True:
            i = text.find(pat, pos)
            if i < 0: break
            print(f"  0x{TEXT_VA+i:06X}: {prefix.hex()} + {nm}")
            pos = i + 1
# also scan for full DWORD refs anywhere in text (e.g. mov [x], va or lea)
print("== any dword == va in .text ==")
for off in range(0, len(text)-3):
    v = struct.unpack_from('<I', text, off)[0]
    if v in font_strings:
        print(f"  0x{TEXT_VA+off:06X}: dword ref -> {font_strings[v]}")
