import struct
b = open(r'E:\Game\ps5\iso\analysis\gamefonta.fnt','rb').read()
recOff, offSec, offBmp = struct.unpack_from('<III', b, 8)
atw, ath = struct.unpack_from('<HH', b, offBmp)
bitmap = b[offBmp+0x434:offBmp+0x434+atw*ath]

def art(y0, y1, x0, x1):
    for y in range(y0, y1):
        row = bitmap[y*atw:(y+1)*atw]
        s = ''.join('#' if row[x] > 100 else ('+' if row[x] > 30 else ('.' if row[x] > 8 else ' ')) for x in range(x0, x1))
        print('%3d: %s' % (y, s))

# 'A' occupies px cols 23..31 (f1/2..f2/2), rows 10..18 (f3/2..f4/2)
# What is at cols 23..31, rows 19..33?
print('=== cols 16..48, rows 8..36 (vertical strip under A) ===')
art(8, 36, 16, 48)
print()
# 'a' at cols 12..19 rows 29..36; M at 45..54 rows 16..24
print('=== full row band 19..26, cols 0..96 (between A and a blocks) ===')
art(19, 27, 0, 98)