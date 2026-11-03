# dump v12 hanzi records + bitmap rects to verify glyph placement
import struct
ANA = r'E:\Game\ps5\iso\analysis'
b = open(f'{ANA}\\gamefonta_v12.fnt', 'rb').read()
cnt, hgt = struct.unpack_from('<HH', b, 0)
nsect, magic, oSec, oBmp = struct.unpack_from('<IIII', b, 4)
atw, ath = struct.unpack_from('<HH', b, oBmp)
act_bm = len(b) - atw * ath
print(f'atlas {atw}x{ath} bm@0x{act_bm:X}')

def dump_rect(code):
    for i in range(cnt):
        p = 0x214 + i * 16
        c, x0, x1, y0, y1, f5, adv, kern = struct.unpack_from('<8H', b, p)
        if c == code:
            print(f'\ncode=0x{code:04X} rect=({x0},{x1},{y0},{y1}) f5={f5} adv={adv} kern=0x{kern:04X}')
            w = x1 - x0; h = y1 - y0
            if w <= 32 and h <= 24:
                for yy in range(max(0, y0), min(ath, y1)):
                    row = ''.join('#' if b[act_bm + yy * atw + xx] > 0 else '.' for xx in range(max(0, x0), min(atw, x1)))
                    print('  ' + row)
            else:
                # sample 5x5 grid
                for gy in range(5):
                    yy = y0 + (y1 - y0) * gy // 5
                    row = ''.join('#' if b[act_bm + yy * atw + xx] > 0 else '.' for xx in range(x0, x1, max(1, w // 40)))
                    print('  ' + row[:60])
            return
    print(f'code 0x{code:04X} not found')

for code in (0x4E00, 0x6211, 0x4F60, 0x7684, 0x662F, 0x4E0D, 0x4E00 + 818):
    dump_rect(code)

# also check f5 range of original latin
print('\norig latin f5/f6:')
for i in range(0, min(10, cnt)):
    p = 0x214 + i * 16
    c, x0, x1, y0, y1, f5, adv, kern = struct.unpack_from('<8H', b, p)
    if c < 0x80:
        print(f'  0x{c:02X} rect=({x0},{x1},{y0},{y1}) f5={f5} adv={adv}')