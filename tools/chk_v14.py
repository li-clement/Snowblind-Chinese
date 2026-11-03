import struct
ANA = r'E:\Game\ps5\iso\analysis'
for nm in ('gamefonta_v14', 'bigfont_v14'):
    b = open(f'{ANA}\\{nm}.fnt', 'rb').read()
    cnt, hgt = struct.unpack_from('<HH', b, 0)
    atw, ath = struct.unpack_from('<HH', b, struct.unpack_from('<I', b, 0x10)[0])
    act_bm = len(b) - atw * ath
    print(f'=== {nm}: cnt={cnt} atlas={atw}x{ath}')
    def dump_rect(code, wmax=40):
        for i in range(cnt):
            p = 0x214 + i * 16
            c, x0, x1, y0, y1, f5, adv, kern = struct.unpack_from('<8H', b, p)
            if c == code:
                w = x1 - x0; h = y1 - y0
                print(f'  code=0x{code:04X} rect=({x0},{x1},{y0},{y1}) w={w} h={h} f5={f5} adv={adv}')
                stride = max(1, w // wmax)
                for yy in range(y0, y1):
                    print('   ', ''.join('#' if b[act_bm + yy * atw + xx] > 0 else '.' for xx in range(x0, x1, stride)))
                return
        print(f'  code 0x{code:04X} NOT FOUND')
    for code in (0x4E00, 0x4E8C, 0x3002, 0xFF0C, 0x2014, 0x2026):
        dump_rect(code)
    # latin baseline check: print f5 of a few
    latin = []
    for i in range(cnt):
        p = 0x214 + i * 16
        c, x0, x1, y0, y1, f5, adv, kern = struct.unpack_from('<8H', b, p)
        if 0x20 <= c < 0x7F:
            latin.append((chr(c), y1 - y0, f5, adv))
    print('  latin sample (ch, h, f5, adv):', latin[:8])