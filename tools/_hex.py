XBE = r"E:\Game\ps5\iso\[XBOX].Baldur's.Gate.Dark.Alliance.[USA]\default.xbe"
b = open(XBE,'rb').read()
TEXT_VA, TEXT_RAW = 0x11000, 0x1000
# file offset within text slice
for va in [0x5F3C0, 0x5F5A0, 0x67E40, 0x68C40, 0x68F10]:
    off = TEXT_RAW + (va - TEXT_VA)
    data = b[off:off+0x60]
    print(f"--- VA 0x{va:X} (file 0x{off:X}) ---")
    for i in range(0, len(data), 16):
        chunk = data[i:i+16]
        hexs = ' '.join(f'{x:02X}' for x in chunk)
        asc = ''.join(chr(x) if 32<=x<127 else '.' for x in chunk)
        print(f"  0x{va+i:06X}: {hexs:<48s} {asc}")
