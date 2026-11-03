import re
b = open(r"E:\Game\ps5\iso\[XBOX].Baldur's.Gate.Dark.Alliance.[USA]\default.xbe", 'rb').read()
TEXT_RAW, TEXT_VA, TEXT_SIZE = 0x1000, 0x11000, 0xDC79C
text = b[TEXT_RAW:TEXT_RAW+TEXT_SIZE]
# absolute-read patterns: mov reg,[abs] -> 8B / A1 with disp32
pats = {
    'mov ecx,[233F44]': b'\x8b\x0d\x44\x3f\x23\x00',
    'mov eax,[233F44]': b'\xa1\x44\x3f\x23\x00',
    'mov edx,[233F44]': b'\x8b\x15\x44\x3f\x23\x00',
    'mov [233F44],eax': b'\xa3\x44\x3f\x23\x00',
    'mov [233F44],ecx': b'\x89\x0d\x44\x3f\x23\x00',
    'mov ecx,[233F48]': b'\x8b\x0d\x48\x3f\x23\x00',
    'mov edx,[233F48]': b'\x8b\x15\x48\x3f\x23\x00',
    'mov [233F48],eax': b'\xa3\x48\x3f\x23\x00',
    'mov ecx,[233F4C]': b'\x8b\x0d\x4c\x3f\x23\x00',
    'mov edx,[233F4C]': b'\x8b\x15\x4c\x3f\x23\x00',
}
for name, pat in pats.items():
    hits = [TEXT_VA + m.start() for m in re.finditer(re.escape(pat), text)]
    if hits:
        print(f'{name}: {[hex(h) for h in hits]}')