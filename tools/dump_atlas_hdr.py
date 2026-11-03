import struct
ANA = r'E:\Game\ps5\iso\analysis'

for name in ('gamefonta', 'gamefontmed', 'gamefontsmall', 'bigfont', 'creditfont'):
    print(f'===== {name} =====')
    b = open(f'{ANA}\\{name}.fnt', 'rb').read()
    cnt, hgt = struct.unpack_from('<HH', b, 0)
    nsect, magic, offSec, offBmp = struct.unpack_from('<IIII', b, 4)
    print(f'  HEAD: cnt={cnt} hgt={hgt} nsect=0x{nsect:X} magic=0x{magic:X} offSec=0x{offSec:X} offBmp=0x{offBmp:X}')
    # atlas header at offBmp: 32 bytes
    atw, ath = struct.unpack_from('<HH', b, offBmp)
    ah = b[offBmp:offBmp + 32]
    print(f'  ATLAS@0x{offBmp:X}: atw={atw} ath={ath} next32={ah.hex()}')
    # u16/u32 interpretations
    u16 = struct.unpack_from('<8H', b, offBmp)
    u32 = struct.unpack_from('<8I', b, offBmp)
    print(f'  u16s: {[hex(x) for x in u16]}')
    print(f'  u32s: {[hex(x) for x in u32]}')
    # bitmap start: file end - atw*ath
    bm = len(b) - atw * ath
    print(f'  bitmap start (file-end calc): 0x{bm:X}')
    # what engine expects: offBmp + 0x400 = ?
    print(f'  offBmp+0x400 = 0x{offBmp + 0x400:X}')
    print(f'  offBmp+4 = 0x{offBmp + 4:X}, offBmp+8 = 0x{offBmp + 8:X}')
    # meta region content 0x14/0x18 fields
    print()