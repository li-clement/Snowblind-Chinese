import struct
p = r"E:\Game\ps5\iso\[XBOX].Baldur's.Gate.Dark.Alliance.[USA]\res\font.lmp"
b = open(p, 'rb').read()
cnt = struct.unpack_from('<I', b, 0)[0]
e = 4
name = b[e:e+0x40].split(b'\x00')[0]
d = struct.unpack_from('<5I', b, e+0x2C)
off = d[3]
nsect = struct.unpack_from('<I', b, off+4)[0]
recOff = struct.unpack_from('<I', b, off+8)[0]
offSec = struct.unpack_from('<I', b, off+0xC)[0]
offBmp = struct.unpack_from('<I', b, off+0x10)[0]
c = struct.unpack_from('<H', b, off)[0]
h = struct.unpack_from('<H', b, off+2)[0]
print('subfile %r at 0x%X: cnt=%d hgt=%d nsect=%d recOff=0x%X offSec=0x%X offBmp=0x%X' % (name, off, c, h, nsect, recOff, offSec, offBmp))
atw, ath = struct.unpack_from('<HH', b, off+offBmp)
print('atlas atw=%d ath=%d (file end 0x%X, bitmap end 0x%X)' % (atw, ath, off+offBmp, off+offBmp+0x434+atw*ath))

# first 12 records
print('\nfirst 14 records (charcode, f1..f6, kernIdx):')
for i in range(14):
    ro = off + recOff + i*16
    vals = struct.unpack_from('<8H', b, ro)
    print('  rec#%3d: %s' % (i, vals))

# last 6 records
print('\nlast 6 records:')
for i in range(c-6, c):
    ro = off + recOff + i*16
    vals = struct.unpack_from('<8H', b, ro)
    print('  rec#%3d: %s' % (i, vals))

# scan charcodes: what range? how many with high bits?
charcodes = [struct.unpack_from('<H', b, off+recOff+i*16)[0] for i in range(c)]
import collections
hi = [x for x in charcodes if x > 0x7FF]
print('\nchars > 0x7FF: %d of %d' % (len(hi), c))
if hi:
    print('  min=%04X max=%04X' % (min(hi), max(hi)))
    hist = collections.Counter(x >> 8 for x in hi)
    print('  high-byte histogram:', sorted(hist.items()))
# check ordering: is charcode[i] == charcode[i-1] + 1?
asc = sum(1 for i in range(1, c) if charcodes[i] == charcodes[i-1] + 1)
print('  sequential-charcode steps: %d/%d' % (asc, c-1))
print('  first 20 charcodes:', [hex(x) for x in charcodes[:20]])
print('  around 0x7FF boundary:', [hex(x) for x in charcodes[0x7F0:0x810]])