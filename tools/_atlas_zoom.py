import struct
b = open(r'E:\Game\ps5\iso\analysis\gamefonta.fnt','rb').read()
cnt, hgt, nsect = struct.unpack_from('<HHI', b, 0)
recOff, offSec, offBmp = struct.unpack_from('<III', b, 8)
atw, ath = struct.unpack_from('<HH', b, offBmp)
bitmap = b[offBmp+0x434:offBmp+0x434+atw*ath]

recs = {}
for i in range(cnt):
    off = recOff + i*16
    ch, f1, f2, f3, f4, f5, f6, kern = struct.unpack_from('<8H', b, off)
    recs[ch] = (f1, f2, f3, f4, f5, f6, kern, i)

def zoom(ch, label):
    f1, f2, f3, f4, f5, f6, kern, i = recs[ch]
    x0, x1, y0, y1 = f1//2, f2//2, f3//2, f4//2
    print('=== %s (rec#%d) halfpx f1..f4=(%d,%d,%d,%d) -> px x=%d..%d y=%d..%d ===' % (label, i, f1,f2,f3,f4, x0,x1,y0,y1))
    # pad 2px around
    for yy in range(max(0,y0-2), min(ath, y1+3)):
        row = bitmap[yy*atw:(yy+1)*atw]
        s = ''.join('#' if v > 100 else ('+' if v > 40 else ('.' if v > 10 else ' ')) for v in row[max(0,x0-2):min(atw, x1+3)])
        print('%3d: %s' % (yy, s))
    print()

if ord('A') in recs: zoom(ord('A'), 'A')
if ord('a') in recs: zoom(ord('a'), 'a')
if ord('0') in recs: zoom(ord('0'), '0')
if ord('g') in recs: zoom(ord('g'), 'g')
if ord('.') in recs: zoom(ord('.'), '.')
if ord('M') in recs: zoom(ord('M'), 'M')