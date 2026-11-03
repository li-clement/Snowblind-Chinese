import struct, os

ANA = r'E:\Game\ps5\iso\analysis'
OUT = r'E:\Game\ps5\iso\analysis'
names = ['gamefonta', 'gamefontmed', 'gamefontsmall', 'bigfont', 'creditfont']

# v7 = v5 with hgt field (offset 2, u16) forced back to 8
for nm in names:
    src = os.path.join(ANA, f'{nm}_v5.fnt')
    dst = os.path.join(OUT, f'{nm}_v7.fnt')
    b = bytearray(open(src, 'rb').read())
    cnt, hgt = struct.unpack_from('<HH', b, 0)
    struct.pack_into('<H', b, 2, 8)  # hgt = 8 like original
    open(dst, 'wb').write(b)
    print(f'{nm}_v7.fnt: cnt={cnt} hgt 16 -> 8, len still {len(b)}')
print('DONE v7')