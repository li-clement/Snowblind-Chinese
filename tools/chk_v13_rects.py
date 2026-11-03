import struct
ANA = r'E:\Game\ps5\iso\analysis'
b = open(f'{ANA}\\gamefonta_v13.fnt', 'rb').read()
cnt, hgt = struct.unpack_from('<HH', b, 0)
nsect, magic, oSec, oBmp = struct.unpack_from('<IIII', b, 4)
atw, ath = struct.unpack_from('<HH', b, oBmp)
act_bm = len(b) - atw * ath
print(f'atlas {atw}x{ath} bm@0x{act_bm:X} cnt={cnt}')

def dump_rect(code, wmax=40):
    for i in range(cnt):
        p = 0x214 + i * 16
        c, x0, x1, y0, y1, f5, adv, kern = struct.unpack_from('<8H', b, p)
        if c == code:
            w = x1 - x0; h = y1 - y0
            print(f'\ncode=0x{code:04X} rect=({x0},{x1},{y0},{y1}) w={w} h={h} f5={f5} adv={adv}')
            # downsample if too wide
            stride = max(1, w // wmax)
            for yy in range(y0, y1):
                row = ''.join('#' if b[act_bm + yy * atw + xx] > 0 else '.' for xx in range(x0, x1, stride))
                print('  ' + row)
            return
    print(f'code 0x{code:04X} not found')

# the previously-blocked flat chars + common ones
for code in (0x4E00, 0x4E8C, 0x4E09, 0x4E0A, 0x4E0B, 0x6211, 0x4F60, 0x7684, 0x4E0D, 0x662F):
    dump_rect(code)