import struct
b = open(r'E:\Game\ps5\iso\analysis\gamefonta.fnt','rb').read()
cnt = struct.unpack_from('<H', b, 0)[0]
recOff, offSec, offBmp = struct.unpack_from('<III', b, 8)
atw, ath = struct.unpack_from('<HH', b, offBmp)
bitmap = b[offBmp+0x434:offBmp+0x434+atw*ath]

recs = {}
for i in range(cnt):
    off = recOff + i*16
    ch, f1, f2, f3, f4, f5, f6, kern = struct.unpack_from('<8H', b, off)
    recs[ch] = (f1, f2, f3, f4, f5, f6, kern, i)

def ink_bbox(x0, x1, y0, y1, thr=60):
    xs, ys = [], []
    for y in range(y0, min(y1, ath)):
        for x in range(x0, min(x1, atw)):
            if bitmap[y*atw+x] > thr:
                xs.append(x); ys.append(y)
    if not xs:
        return None
    return (min(xs), max(xs), min(ys), max(ys))

for ch, nm in ((ord('A'),'A'), (ord('a'),'a'), (ord('0'),'0'), (ord('M'),'M'), (ord('W'),'W'), (ord('g'),'g'), (ord('.'),'.'), (ord('j'),'j'), (ord('l'),'l')):
    f1, f2, f3, f4, f5, f6, kern, i = recs[ch]
    boxA = ink_bbox(f1//2-4, f2//2+4, f3//2-4, f4//2+4)
    boxB = ink_bbox(f1-8, f2+8, f3-8, f4+8)
    boxC = ink_bbox(f1//4-4, f2//4+4, f3//4-4, f4//4+4)
    print('%s rec#%d f=(%d,%d,%d,%d,%d,%d):' % (nm, i, f1,f2,f3,f4,f5,f6))
    print('   /2 box(%d..%d, %d..%d) -> ink %s' % (f1//2, f2//2, f3//2, f4//2, boxA))
    print('   /1 box(%d..%d, %d..%d) -> ink %s' % (f1, f2, f3, f4, boxB))
    print('   /4 box(%d..%d, %d..%d) -> ink %s' % (f1//4, f2//4, f3//4, f4//4, boxC))