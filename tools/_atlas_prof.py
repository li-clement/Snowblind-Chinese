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

# Find ink bounding box for candidate glyph by looking at unique column/row patterns.
# Print column profile (any ink per col) and row profile (any ink per row) for select chars.
def profiles(ch):
    f1, f2, f3, f4, f5, f6, kern, i = recs[ch]
    print('char %r rec#%d f=%s' % (chr(ch), i, (f1,f2,f3,f4)))
    cands = [(f1//2, f2//2, f3//2, f4//2), (f1, f2, f3, f4)]
    for (x0,x1,y0,y1) in cands:
        print('  box x%d..%d y%d..%d' % (x0,x1,y0,y1))
        # row profile in the box columns + a bit
        seg = bitmap
        for scale, fname in ((1,'raw'), (2,'half')):
            pass
    # rows: ink count per row for full width 0..60, mark predicted start/end for /1 and /2
    xpred2 = (f1//2, f2//2)
    xpred1 = (f1, f2)
    print('  col profile 0..60:')
    xs=[]
    for x in range(0, 64):
        cnt = sum(1 for y in range(0, 45) if bitmap[y*atw+x] > 80)
        xs.append('%d:%d' % (x, cnt))
    print('   '+''.join(xs))
    print('  row profile 0..45:')
    for y in range(0, 46):
        c = sum(1 for x in range(0, 128) if bitmap[y*atw+x] > 80)
        mark = ''
        if y == f3//2: mark += ' <f3/2'
        if y == f4//2: mark += ' <f4/2'
        if y == f3: mark += ' <f3'
        if y == f4: mark += ' <f4'
        print('%3d:%2d%s' % (y, c, mark))

for ch in (ord('A'),):
    profiles(ch)