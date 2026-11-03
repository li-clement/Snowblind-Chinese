import struct
import os
ANA = r'E:\Game\ps5\iso\analysis'

def chk(name, fp):
    b = open(fp, 'rb').read()
    cnt, hgt = struct.unpack_from('<HH', b, 0)
    nsect, magic, offSec, offBmp = struct.unpack_from('<IIII', b, 4)
    atw, ath = struct.unpack_from('<HH', b, offBmp)
    flags = struct.unpack_from('<H', b, offBmp + 4)[0]   # [atlas+4] u16
    off8 = struct.unpack_from('<I', b, offBmp + 8)[0]    # [atlas+8] u32
    engine_bm = offBmp + off8 + 0x400                    # engine's bitmap start
    actual_bm = len(b) - atw * ath                       # where we put it
    print(f'  {name}: cnt={cnt} hgt={hgt} nsect=0x{nsect:X} magic=0x{magic:X} offRec~0x214')
    print(f'    atw={atw} ath={ath} flags=[atlas+4]=0x{flags:04X} (0x4000? {"YES" if flags & 0x4000 else "NO!!"})')
    print(f'    [atlas+8]=0x{off8:X}  engine_bitmap=0x{engine_bm:X}  actual_bitmap=0x{actual_bm:X}  {"MATCH" if engine_bm == actual_bm else "<<< MISMATCH diff=0x%X" % (actual_bm - engine_bm)}')

for name in ('gamefonta', 'gamefontmed', 'gamefontsmall', 'bigfont', 'creditfont'):
    print(f'== ORIGINAL {name} ==')
    chk(name, f'{ANA}\\{name}.fnt')

print()
for name in ('gamefonta_v8', 'gamefontmed_v8', 'gamefontsmall_v8', 'bigfont_v8', 'creditfont_v8'):
    fp = f'{ANA}\\{name}.fnt'
    if os.path.exists(fp):
        print(f'== V8 {name} ==')
        chk(name, fp)