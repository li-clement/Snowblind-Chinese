import re
b = open(r"E:\Game\ps5\iso\[XBOX].Baldur's.Gate.Dark.Alliance.[USA]\default.xbe", 'rb').read()
TEXT_RAW, TEXT_VA = 0x1000, 0x11000
text = b[TEXT_RAW:TEXT_RAW + 0xDC79C]

# string VAs for font files / lmps (from find_strings earlier)
for label, va in [('gamefonta.fnt', 0x13ED88), ('gamefontmed.fnt', 0x13ED70), ('gamefontsmall.fnt', 0x13ED98),
                  ('bigfont.fnt', 0x13EDB0), ('creditfont.fnt', 0x13EDC8),
                  ('font.lmp', 0x13EDE0), ('frontend.lmp', 0x13EDF8)]:
    pat = bytes([va & 0xFF, (va >> 8) & 0xFF, (va >> 16) & 0xFF, (va >> 24) & 0xFF])
    hits = [TEXT_VA + m.start() for m in re.finditer(re.escape(pat), text)]
    print(f'{label} (0x{va:X}): {[hex(h) for h in hits]}')