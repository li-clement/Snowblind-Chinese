import struct
ANA = r'E:\Game\ps5\iso\analysis'
RES = r"E:\Game\ps5\iso\[XBOX].Baldur's.Gate.Dark.Alliance.[USA]\res"

# 1. verify v10 font
b = open(f'{ANA}\\gamefonta_v10.fnt', 'rb').read()
cnt, hgt = struct.unpack_from('<HH', b, 0)
nsect, magic, oSec, oBmp = struct.unpack_from('<IIII', b, 4)
atw, ath = struct.unpack_from('<HH', b, oBmp)
flags = struct.unpack_from('<H', b, oBmp + 4)[0]
off8 = struct.unpack_from('<I', b, oBmp + 8)[0]
eng_bm = oBmp + off8 + 0x400
act_bm = len(b) - atw * ath
print(f'v10 fnt: cnt={cnt} hgt={hgt} nsect=0x{nsect:X} magic=0x{magic:X} offSec=0x{oSec:X} offBmp=0x{oBmp:X}')
print(f'  atw={atw} ath={ath} flags=0x{flags:04X} (0x4000? {bool(flags & 0x4000)}) [a+8]=0x{off8:X}')
print(f'  engine_bm=0x{eng_bm:X} actual_bm=0x{act_bm:X} match={eng_bm == act_bm} size={len(b)}')
# record sanity: first 3 + last 3
for i in (0, 1, 2, cnt - 3, cnt - 2, cnt - 1):
    p = 0x214 + i * 16
    code = struct.unpack_from('<H', b, p)[0]
    r = b[p:p + 16].hex()
    print(f'  rec[{i}] code=0x{code:04X} {r}')
# check code uniqueness in 0x2E7..0x942 ext zone
ext_codes = set()
dupe = 0
for i in range(141, 1824):
    c = struct.unpack_from('<H', b, 0x214 + i * 16)[0]
    if c in ext_codes:
        dupe += 1
    ext_codes.add(c)
print(f'  ext records unique: {dupe == 0}')

# 2. verify font.lmp layout
lb = open(f'{RES}\\font.lmp', 'rb').read()
c = struct.unpack_from('<I', lb, 0)[0]
cur = 4 + c * 64
cur = (cur + 0x7F) & ~0x7F
ok = True
for i in range(c):
    p = 4 + i * 64
    nm = lb[p:p + 56].split(b'\x00', 1)[0].decode('latin1')
    off, sz = struct.unpack_from('<II', lb, p + 56)
    if not (off == cur and off % 0x80 == 0 and off + sz <= len(lb)):
        ok = False
    print(f'  {nm:<22s} off=0x{off:X} sz={sz} exp=0x{cur:X} {"OK" if off == cur else "BAD"}')
    cur = (off + sz + 0x7F) & ~0x7F
print(f'font.lmp layout valid: {ok} size={len(lb)}')