import struct, os
BACK = r'E:\Game\ps5\iso\backup_original'

for lmp in ('font.lmp', 'frontend.lmp'):
    b = open(os.path.join(BACK, lmp), 'rb').read()
    cnt = struct.unpack_from('<I', b, 0)[0]
    print(f'== {lmp} ({len(b)}B, {cnt} entries) ==')
    for i in range(cnt):
        p = 4 + i * 64
        nm = b[p:p + 56].split(b'\0', 1)[0].decode('latin1')
        off, size = struct.unpack_from('<II', b, p + 56)
        print(f'  {i:3d} {nm:<24s} off=0x{off:X} size={size} ({size/1024:.1f}KB)')