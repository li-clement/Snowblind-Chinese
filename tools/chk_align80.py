import struct
def chk(path, label):
    b = open(path, 'rb').read()
    c = struct.unpack_from('<I', b, 0)[0]
    bad = []
    for i in range(c):
        p = 4 + i * 64
        off, sz = struct.unpack_from('<II', b, p + 56)
        if off % 0x80:
            bad.append((i, hex(off)))
    print(f'{label}: {c} entries 0x80-aligned={len(bad) == 0} bad={bad[:6]}')

chk(r'E:\Game\ps5\iso\backup_original\font.lmp', 'ORIG font.lmp')
chk(r'E:\Game\ps5\iso\backup_original\frontend.lmp', 'ORIG frontend.lmp')
chk(r"E:\Game\ps5\iso\[XBOX].Baldur's.Gate.Dark.Alliance.[USA]\res\font.lmp", 'CUR  font.lmp (v8)')
chk(r"E:\Game\ps5\iso\[XBOX].Baldur's.Gate.Dark.Alliance.[USA]\res\frontend.lmp", 'CUR  frontend.lmp (v8)')