import struct
ANA = r'E:\Game\ps5\iso\analysis'
RES = r"E:\Game\ps5\iso\[XBOX].Baldur's.Gate.Dark.Alliance.[USA]\res"

for nm in ('gamefonta_v12', 'gamefontmed_v12', 'gamefontsmall_v12'):
    b = open(f'{ANA}\\{nm}.fnt', 'rb').read()
    cnt, hgt = struct.unpack_from('<HH', b, 0)
    nsect, magic, oSec, oBmp = struct.unpack_from('<IIII', b, 4)
    atw, ath = struct.unpack_from('<HH', b, oBmp)
    flags = struct.unpack_from('<H', b, oBmp + 4)[0]
    off8 = struct.unpack_from('<I', b, oBmp + 8)[0]
    eng_bm = oBmp + off8 + 0x400
    act_bm = len(b) - atw * ath
    bad = 0
    for i in range(cnt):
        p = 0x214 + i * 16
        c, x0, x1, y0, y1, f5, adv, kern = struct.unpack_from('<8H', b, p)
        if x1 <= x0 or y1 <= y0:
            continue
        if x1 > atw or y1 > ath:
            bad += 1
    print(f'{nm}: cnt={cnt} hgt={hgt} atlas={atw}x{ath} pow2={1<<(atw-1).bit_length()}x{1<<(ath-1).bit_length()} flags=0x{flags:04X} bm_match={eng_bm==act_bm} bad_rects={bad} size={len(b)}')

lb = open(f'{RES}\\font.lmp', 'rb').read()
c = struct.unpack_from('<I', lb, 0)[0]
cur = 4 + c * 64
cur = (cur + 0x7F) & ~0x7F
ok = True
names = []
for i in range(c):
    p = 4 + i * 64
    nm = lb[p:p + 56].split(b'\x00', 1)[0].decode('latin1')
    off, sz = struct.unpack_from('<II', lb, p + 56)
    if off != cur or off % 0x80 != 0:
        ok = False
    names.append(nm)
    cur = (off + sz + 0x7F) & ~0x7F
print('lmp entries:', names)
print('lmp valid:', ok, 'size', len(lb))