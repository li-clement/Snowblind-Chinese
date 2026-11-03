import struct
b = open(r'E:\Game\ps5\iso\analysis\gamefonta.fnt','rb').read()
cnt, hgt, nsect = struct.unpack_from('<HHI', b, 0)
recOff, offSec, offBmp = struct.unpack_from('<III', b, 8)
atw, ath = struct.unpack_from('<HH', b, offBmp)
bitmapOff = offBmp + 0x434
print('cnt=%d hgt=%d atw=%d ath=%d bitmap@0x%X, file size=%d, expected bits=%d' % (cnt, hgt, atw, ath, bitmapOff, len(b), atw*ath))

# records
recs = {}
for i in range(cnt):
    off = recOff + i*16
    ch, f1, f2, f3, f4, f5, f6, kern = struct.unpack_from('<8H', b, off)
    recs[ch] = (f1, f2, f3, f4, f5, f6, kern, i)

# atlas character positions (half-pixel units -> pixels /2)
for ch, nm in ((ord('A'),'A'), (ord('a'),'a'), (ord('0'),'0'), (ord('M'),'M'), (ord('W'),'W'), (ord('g'),'g'), (ord('.'),'.')):
    if ch in recs:
        f1, f2, f3, f4, f5, f6, kern, i = recs[ch]
        print('%s: rec#%d f1=%d f2=%d f3=%d f4=%d f5=%d f6=%d (pixels: x=%d..%d+1 y=%d..%d+1 w=%d h=%d)' % (nm, i, f1,f2,f3,f4,f5,f6, f1//2, f2//2, f3//2, f4//2, (f2-f1)//2, (f4-f3)//2))

bitmap = b[bitmapOff:bitmapOff+atw*ath]
def row_art(y0, y1):
    for yy in range(y0, y1):
        row = bitmap[yy*atw:(yy+1)*atw]
        s = ''.join('#' if v > 100 else ('+' if v > 40 else ('.' if v > 10 else ' ')) for v in row)
        print('%3d: %s' % (yy, s[:80]))

print('\n--- rows around A (f3/2=10, expected height 8) ---')
row_art(6, 20)
print('\n--- rows around a (f3/2=29) ---')
row_art(26, 38)
print('\n--- rows around 0 (f3/2=0) ---')
row_art(0, 12)