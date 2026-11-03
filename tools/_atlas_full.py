import struct
b = open(r'E:\Game\ps5\iso\analysis\gamefonta.fnt','rb').read()
cnt, hgt, nsect = struct.unpack_from('<HHI', b, 0)
recOff, offSec, offBmp = struct.unpack_from('<III', b, 8)
atw, ath = struct.unpack_from('<HH', b, offBmp)
bitmap = b[offBmp+0x434:offBmp+0x434+atw*ath]
print('atw=%d ath=%d' % (atw, ath))

recs = {}
for i in range(cnt):
    off = recOff + i*16
    ch, f1, f2, f3, f4, f5, f6, kern = struct.unpack_from('<8H', b, off)
    recs[ch] = (f1, f2, f3, f4, f5, f6, kern, i)

# precompute the pixel box (raw f values, not /2) for each char
boxes = {}
for ch, r in recs.items():
    f1, f2, f3, f4, f5, f6, kern, i = r
    boxes[ch] = (f1, f2, f3, f4)

# full atlas: print every 2nd row, every 2nd col (128 chars) with col labels
def art(rows, c0, c1):
    print('cols %d..%d' % (c0, c1))
    print('     ' + ''.join(str((c//10)%10) if c%10==0 else ' ' for c in range(c0, c1, 2)))
    print('     ' + ''.join(str(c%10) for c in range(c0, c1, 2)))
    for y in rows:
        row = bitmap[y*atw:(y+1)*atw]
        s = ''.join('#' if row[c] > 100 else ('+' if row[c] > 30 else '.') for c in range(c0, c1, 2))
        print('%3d  %s' % (y, s))

art(range(0, 40), 0, 128)
print()
art(range(0, 40), 128, 256)