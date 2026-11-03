import struct

def parse_lmp(path):
    b = open(path, 'rb').read()
    print('== %s: size=0x%X' % (path, len(b)))
    cnt = struct.unpack_from('<I', b, 0)[0]
    print('   entry count: %d' % cnt)
    print('   first 0x40 bytes:', ' '.join('%02X' % x for x in b[:0x40]))
    return b

for p in [r'E:\Game\ps5\iso\backup_original\font.lmp', r'E:\Game\ps5\iso\[XBOX].Baldur''s.Gate.Dark.Alliance.[USA]\res\font.lmp']:
    b = parse_lmp(p)
    cnt = struct.unpack_from('<I', b, 0)[0]
    for i in range(cnt):
        e = 4 + i*0x40
        name = b[e:e+0x40].split(b'\x00')[0]
        if name in (b'gamefonta.fnt', b'gamefontmed.fnt', b'gamefontsmall.fnt', b'bigfont.fnt', b'creditfont.fnt'):
            d = struct.unpack_from('<5I', b, e+0x2C)
            off38, off3C = d[3], d[4]
            print('   %s -> +0x38=0x%X +0x3C=0x%X' % (name, off38, off3C))
            if off38 < len(b):
                print('     header:', ' '.join('%02X' % x for x in b[off38:off38+0x20]))
                if name == b'gamefonta.fnt':
                    print('     u32s:', [hex(x) for x in struct.unpack_from('<8I', b, off38)])
    print()