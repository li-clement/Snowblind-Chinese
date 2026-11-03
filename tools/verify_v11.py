import struct
ANA = r'E:\Game\ps5\iso\analysis'
RES = r"E:\Game\ps5\iso\[XBOX].Baldur's.Gate.Dark.Alliance.[USA]\res"

b = open(f'{ANA}\\gamefonta_v11.fnt', 'rb').read()
cnt, hgt = struct.unpack_from('<HH', b, 0)
nsect, magic, oSec, oBmp = struct.unpack_from('<IIII', b, 4)
atw, ath = struct.unpack_from('<HH', b, oBmp)
flags = struct.unpack_from('<H', b, oBmp + 4)[0]
off8 = struct.unpack_from('<I', b, oBmp + 8)[0]
eng_bm = oBmp + off8 + 0x400
act_bm = len(b) - atw * ath
print(f'v11: cnt={cnt} hgt={hgt} magic=0x{magic:X} offSec=0x{oSec:X} offBmp=0x{oBmp:X}')
print(f'  atw={atw} ath={ath} flags=0x{flags:04X} 0x4000={bool(flags & 0x4000)} [a+8]=0x{off8:X}')
print(f'  eng_bm=0x{eng_bm:X} act_bm=0x{act_bm:X} match={eng_bm == act_bm} size={len(b)}')

# verify hanzi record rects lie inside atlas and point at non-empty bitmap area
bitmap_start = act_bm
bad = 0
sample = []
for i in range(cnt):
    p = 0x214 + i * 16
    c, x0, x1, y0, y1, f5, adv, kern = struct.unpack_from('<8H', b, p)
    if c == 32 or (x1 <= x0 or y1 <= y0):
        continue
    if x1 > atw or y1 > ath:
        bad += 1
        continue
    # sample center pixel
    cx = (x0 + x1) // 2; cy = (y0 + y1) // 2
    v = b[bitmap_start + cy * atw + cx]
    if v == 0:
        # try scanning 5x5 around center
        found = 0
        for yy in range(max(0, y0), min(ath, y1)):
            for xx in range(max(0, x0), min(atw, x1)):
                if b[bitmap_start + yy * atw + xx] > 0:
                    found = 1
                    break
            if found:
                break
        if not found:
            bad += 1
    if len(sample) < 8 and c > 0xFF:
        sample.append((hex(c), x0, x1, y0, y1, adv))
print(f'rects out-of-atlas or empty: {bad}')
print('hanzi samples (code,x0,x1,y0,y1,adv):')
for s in sample:
    print('  ', s)

# lmp check
lb = open(f'{RES}\\font.lmp', 'rb').read()
c = struct.unpack_from('<I', lb, 0)[0]
cur = 4 + c * 64
cur = (cur + 0x7F) & ~0x7F
ok = True
for i in range(c):
    p = 4 + i * 64
    nm = lb[p:p + 56].split(b'\x00', 1)[0].decode('latin1')
    off, sz = struct.unpack_from('<II', lb, p + 56)
    if not (off == cur and off % 0x80 == 0):
        ok = False
    print(f'  {nm:<20s} off=0x{off:X} sz={sz} {"OK" if off==cur else "BAD"}')
    cur = (off + sz + 0x7F) & ~0x7F
print('lmp layout valid:', ok, 'size', len(lb))