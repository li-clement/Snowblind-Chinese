# 1) dump v13 latin punct records to confirm adv/sc bug
# 2) collect all punctuation/symbol chars from translations
import struct, os, json, glob

ANA = r'E:\Game\ps5\iso\analysis'
b = open(f'{ANA}\\gamefonta_v13.fnt', 'rb').read()
cnt, hgt = struct.unpack_from('<HH', b, 0)
nsect, magic, oSec, oBmp = struct.unpack_from('<IIII', b, 4)
atw, ath = struct.unpack_from('<HH', b, oBmp)
act_bm = len(b) - atw * ath

print('--- v13 latin punct records (gamefonta) ---')
for i in range(cnt):
    p = 0x214 + i * 16
    c, x0, x1, y0, y1, f5, adv, kern = struct.unpack_from('<8H', b, p)
    if c in (0x21, 0x2C, 0x2E, 0x3F, 0x27, 0x2D, 0x28, 0x29, 0x22):
        print(f'  0x{c:02X} {chr(c)!r} rect=({x0},{x1},{y0},{y1}) w={x1-x0} h={y1-y0} f5={f5} adv={adv}')
        if x1 - x0 <= 16 and y1 - y0 <= 12:
            for yy in range(y0, y1):
                print('   ', ''.join('#' if b[act_bm + yy * atw + xx] > 0 else '.' for xx in range(x0, x1)))

print('\n--- punctuation set in translations ---')
BASE = r'E:\Game\ps5\iso'
TR = os.path.join(BASE, 'translation')
chars = set()
for p in glob.glob(os.path.join(TR, 'zh_*.uni.json')) + glob.glob(os.path.join(TR, 'zh_gtext_part*.uni.json')):
    try:
        obj = json.load(open(p, encoding='utf-8'))
    except Exception:
        continue
    for v in obj.values():
        for ch in v:
            o = ord(ch)
            if o < 0x20 or (0x20 <= o < 0x80) or (0x4E00 <= o <= 0x9FFF):
                continue
            chars.add(ch)
punct = sorted(chars)
print(f'count={len(punct)}')
print(''.join(punct))
# save
open(os.path.join(BASE, 'translation', 'jobs', 'zh_punct.txt'), 'w', encoding='utf-8').write(''.join(punct))
print('saved zh_punct.txt')