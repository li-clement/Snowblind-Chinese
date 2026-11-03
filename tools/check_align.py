import struct, os
RES = r"E:\Game\ps5\iso\[XBOX].Baldur's.Gate.Dark.Alliance.[USA]\res"
BACK = r'E:\Game\ps5\iso\backup_original'

for lmp in ('font.lmp', 'frontend.lmp'):
    for tag, path in (('ORIG', os.path.join(BACK, lmp)), ('CUR ', os.path.join(RES, lmp))):
        b = open(path, 'rb').read()
        c = struct.unpack_from('<I', b, 0)[0]
        ok = True
        for i in range(c):
            p = 4 + i*64
            off, sz = struct.unpack_from('<II', b, p+56)
            if off % 0x100:
                ok = False
                nm = b[p:p+56].split(b'\0',1)[0].decode('latin1')
                print(f'  {tag} {lmp} ENTRY #{i} {nm}: off=0x{off:X} NOT 0x100-aligned!')
        print(f'{tag} {lmp}: {len(b)}B {c} entries -> all 0x100 aligned: {ok}')
    print()