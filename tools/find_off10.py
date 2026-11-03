import re
b = open(r"E:\Game\ps5\iso\[XBOX].Baldur's.Gate.Dark.Alliance.[USA]\default.xbe", 'rb').read()
TEXT_RAW, TEXT_VA, TEXT_SIZE = 0x1000, 0x11000, 0xDC79C
text = b[TEXT_RAW:TEXT_RAW+TEXT_SIZE]
pats = {
  'mov eax,[esi+10]': b'\x8b\x46\x10',
  'mov ecx,[esi+10]': b'\x8b\x4e\x10',
  'mov edx,[esi+10]': b'\x8b\x56\x10',
  'mov eax,[edi+10]': b'\x8b\x47\x10',
  'mov ecx,[edi+10]': b'\x8b\x4f\x10',
  'mov eax,[ebx+10]': b'\x8b\x43\x10',
  'mov eax,[ebp+10]': b'\x8b\x45\x10',
}
for name, pat in pats.items():
    hits = [TEXT_VA + m.start() for m in re.finditer(re.escape(pat), text)]
    if hits:
        print(f'{name}: {[hex(h) for h in hits]}')