import struct
BACK = r'E:\Game\ps5\iso\backup_original'
for nm in ('gamefonta.fnt', 'gamefontmed.fnt', 'gamefontsmall.fnt'):
    b = open(f'{BACK}\\font.lmp', 'rb').read()  # need entries! use analysis copies instead
import os
ANA = r'E:\Game\ps5\iso\analysis'
for nm in ('gamefonta', 'gamefontmed', 'gamefontsmall'):
    # find original font files in analysis (they were extracted earlier?) or backup lmp
    p = f'{ANA}\\{nm}.fnt'
    if os.path.exists(p):
        b = open(p, 'rb').read()
        cnt, hgt = struct.unpack_from('<HH', b, 0)
        nsect, magic, oSec, oBmp = struct.unpack_from('<IIII', b, 4)
        atw, ath = struct.unpack_from('<HH', b, oBmp)
        print(f'{nm}: size={len(b)} cnt={cnt} hgt={hgt} magic=0x{magic:X} offSec=0x{oSec:X} offBmp=0x{oBmp:X} atlas={atw}x{ath}')
    else:
        print(f'{nm}: MISSING {p}')