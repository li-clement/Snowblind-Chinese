import struct
from collections import Counter
ANA = r'E:\Game\ps5\iso\analysis'

for name in ('gamefonta', 'gamefontmed', 'gamefontsmall', 'bigfont', 'creditfont'):
    b = open(f'{ANA}\\{name}.fnt', 'rb').read()
    cnt, hgt = struct.unpack_from('<HH', b, 0)
    _, _, offSec, offBmp = struct.unpack_from('<IIII', b, 4)
    atw, ath = struct.unpack_from('<HH', b, offBmp)
    bmp_off = offBmp + 4 + 1076
    bmp = b[bmp_off:bmp_off + atw * ath]
    c = Counter(bmp)
    top = c.most_common(12)
    print(f'{name}: cnt={cnt} atw={atw} ath={ath} lum-min/max={min(bmp)}/{max(bmp)} top={top}')
    # sample a few non-black pixel VALUES at glyph area of 'A' in gamefonta
    if name == 'gamefonta':
        # rec for 'A': code 0x41 at index? find
        for i in range(cnt):
            p = 0x214 + i*16
            code = struct.unpack_from('<H', b, p)[0]
            if code == 0x41:
                x0, x1, y0, y1 = struct.unpack_from('<HHHH', b, p+2)
                print(f'  "A" rec@0x{p:X}: rect=({x0},{x1},{y0},{y1})')
                vals = Counter(bmp[x0 + y*atw] for y in range(y0, y1) for x in range(x0, x1))
                print(f'  "A" bmp vals: {vals.most_common(12)}')
                break