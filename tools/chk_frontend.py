import struct, os
BACK = r'E:\Game\ps5\iso\backup_original'

def parse_lmp(b):
    c = struct.unpack_from('<I', b, 0)[0]
    out = []
    for i in range(c):
        p = 4 + i * 64
        nm = b[p:p + 56].split(b'\x00', 1)[0].decode('latin1')
        off, size = struct.unpack_from('<II', b, p + 56)
        out.append([nm, off, size])
    return out, c

fb = open(os.path.join(BACK, 'frontend.lmp'), 'rb').read()
ents, cnt = parse_lmp(fb)
print('frontend.lmp entries:')
for nm, off, sz in ents:
    print(f'  {nm:24s} off=0x{off:X} size={sz}')

# dump bigfont header + a few records
try:
    nm, off, sz = next(e for e in ents if e[0] == 'bigfont.fnt')
    b = fb[off:off + sz]
    cntf, hgt = struct.unpack_from('<HH', b, 0)
    nsect, magic, oSec, oBmp = struct.unpack_from('<IIII', b, 4)
    atw, ath = struct.unpack_from('<HH', b, oBmp)
    print(f'\nbigfont: cnt={cntf} hgt={hgt} magic=0x{magic:X} offSec=0x{oSec:X} offBmp=0x{oBmp:X} atlas={atw}x{ath} size={sz}')
    for i in range(min(8, cntf)):
        p = 0x214 + i * 16
        c, x0, x1, y0, y1, f5, adv, kern = struct.unpack_from('<8H', b, p)
        print(f'  0x{c:02X} {chr(c) if 32<=c<127 else "?"!r} rect=({x0},{x1},{y0},{y1}) w={x1-x0} h={y1-y0} f5={f5} adv={adv}')
except StopIteration:
    print('no bigfont in frontend.lmp')
    # maybe gtext fonts stored elsewhere; try creditfont
    for nm2 in ('creditfont.fnt', 'gamefontsmall.fnt'):
        try:
            nm, off, sz = next(e for e in ents if e[0] == nm2)
            b = fb[off:off + sz]
            cntf, hgt = struct.unpack_from('<HH', b, 0)
            nsect, magic, oSec, oBmp = struct.unpack_from('<IIII', b, 4)
            atw, ath = struct.unpack_from('<HH', b, oBmp)
            print(f'{nm2}: cnt={cntf} hgt={hgt} atlas={atw}x{ath} size={sz}')
        except StopIteration:
            print(f'{nm2}: not found')