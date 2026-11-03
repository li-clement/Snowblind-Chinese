import struct, os
ANA = r'E:\Game\ps5\iso\analysis'

def meta_chk(name, fp):
    b = open(fp, 'rb').read()
    cnt, hgt = struct.unpack_from('<HH', b, 0)
    nsect, magic, offSec, offBmp = struct.unpack_from('<IIII', b, 4)
    atw, ath = struct.unpack_from('<HH', b, offBmp)
    meta = b[offBmp + 4:offBmp + 4 + 128]
    u32 = struct.unpack_from('<32I', b, offBmp + 4)
    print(f'-- {name}: offBmp=0x{offBmp:X} atw={atw} ath={ath}')
    print(f'   [atlas+0x14](u32@20)=0x{u32[5]:X}  [atlas+8]=0x{u32[2]:X}  flags=0x{u32[0] & 0xFFFF:04X}')
    # first 8 u32 of meta
    print(f'   meta u32[0..8]: {[hex(x) for x in u32[:8]]}')

meta_chk('orig gamefonta', f'{ANA}\\gamefonta.fnt')
meta_chk('v8 gamefonta', f'{ANA}\\gamefonta_v8.fnt')
print()

# What is at 0xC9BE1 / 0xC9BE2? disassemble
# (will be done via xbe_dis separately)