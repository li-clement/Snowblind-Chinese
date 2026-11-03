import struct, glob

def parse_lmp(path):
    b = open(path, 'rb').read()
    print('== %s: size=0x%X' % (path, len(b)))
    cnt = struct.unpack_from('<I', b, 0)[0]
    print('   entry count: %d' % cnt)
    for i in range(cnt):
        e = 4 + i*0x40
        name = b[e:e+0x40].split(b'\x00')[0]
        d = struct.unpack_from('<5I', b, e+0x2C)
        off38, off3C = d[3], d[4]
        print('   entry %d name=%r +0x38=0x%X +0x3C=0x%X' % (i, name, off38, off3C))
        if off38 + 0x20 <= len(b):
            hdr = b[off38:off38+0x20]
            print('      header:', ' '.join('%02X' % x for x in hdr))
            print('      u32s:', [hex(x) for x in struct.unpack_from('<8I', b, off38)])
    print()

for p in glob.glob(r'E:\Game\ps5\iso\**\font.lmp', recursive=True):
    parse_lmp(p)