# v10 DISCRIMINATOR: original gamefonta body, but cnt extended 141 -> 1824 records.
# Bitmap/atlas/meta = 100% ORIGINAL (256x158, flags 0xC044, [a+8]=0x38).
# New records 141..1823 get code=0x2E7+i, rect = 'A' glyph rect from original.
# frontend.lmp + other fonts = original. Tests whether record COUNT is the breaker.
import struct, os

BASE = r'E:\Game\ps5\iso'
RES = os.path.join(BASE, "[XBOX].Baldur's.Gate.Dark.Alliance.[USA]", 'res')
BACK = os.path.join(BASE, 'backup_original')
ANA = os.path.join(BASE, 'analysis')
ALIGN = 0x80

# ---- 1. build gamefonta_v10.fnt from ORIGINAL gamefonta.fnt ----
src = open(os.path.join(ANA, 'gamefonta.fnt'), 'rb').read()
cnt0, hgt0 = struct.unpack_from('<HH', src, 0)
nsect0, magic0, oSec0, oBmp0 = struct.unpack_from('<IIII', src, 4)
atw, ath = struct.unpack_from('<HH', src, oBmp0)
print(f'orig: cnt={cnt0} hgt={hgt0} magic=0x{magic0:X} offSec=0x{oSec0:X} offBmp=0x{oBmp0:X} atw={atw} ath={ath} size={len(src)}')

NEWCNT = 1824
rec_start = 0x214
new_recs = rec_start + NEWCNT * 16          # 0x7414
new_osec = new_recs
# copy kerning region from original (oSec..oBmp), same length
kern = src[oSec0:oBmp0]
new_obmp = new_osec + len(kern)             # 0x74BC
# atlas header+meta from original (oBmp0..bitmap_start)
bitmap0 = len(src) - atw * ath
atlas_meta = src[oBmp0:bitmap0]             # 4 + 1076 bytes
new_bmp = new_obmp + len(atlas_meta)        # 0x78F4
bitmap = src[bitmap0:bitmap0 + atw * ath]

out = bytearray()
out += struct.pack('<HHIIII', NEWCNT, hgt0, nsect0, magic0, new_osec, new_obmp)
# header padding 0x14..0x214 = copy from original (it contains pre fields)
assert len(out) == 0x14
out += src[0x14:0x214]
assert len(out) == rec_start
# records: first 141 = original, then extended
orig_recs = src[rec_start:rec_start + cnt0 * 16]
out += orig_recs
# 'A' rect from original gamefonta record (code 0x41)
a_rec = None
p = rec_start
for i in range(cnt0):
    code = struct.unpack_from('<H', src, p)[0]
    if code == 0x41:
        a_rec = src[p:p + 16]
        break
    p += 16
assert a_rec is not None
# extend: code 0x2E7.. (hangul-ish zone empty in original), rect = 'A'
for i in range(NEWCNT - cnt0):
    rec = bytearray(a_rec)
    struct.pack_into('<H', rec, 0, 0x2E7 + i)   # sparse codes
    out += rec
assert len(out) == new_recs
out += kern
assert len(out) == new_osec + len(kern)
out += atlas_meta
assert len(out) == new_bmp
out += bitmap
print(f'v10 gamefonta: cnt={NEWCNT} offSec=0x{new_osec:X} offBmp=0x{new_obmp:X} bitmap=0x{new_bmp:X} size={len(out)}')
print(f'  engine bitmap calc: offBmp+0x38+0x400 = 0x{new_obmp + 0x38 + 0x400:X}  actual=0x{new_bmp:X}  match={new_obmp + 0x38 + 0x400 == new_bmp}')
open(os.path.join(ANA, 'gamefonta_v10.fnt'), 'wb').write(bytes(out))

# ---- 2. rebuild font.lmp: gamefonta->v10, med/small ORIGINAL. 0x80 recursive layout ----
def parse_lmp(b):
    cnt = struct.unpack_from('<I', b, 0)[0]
    out = []
    for i in range(cnt):
        pp = 4 + i * 64
        nm = b[pp:pp + 56].split(b'\x00', 1)[0].decode('latin1')
        off, size = struct.unpack_from('<II', b, pp + 56)
        out.append([nm, off, size])
    return out, cnt

def build(names, blobs):
    n = len(names)
    hdr_len = 4 + n * 64
    cur = hdr_len
    if cur % ALIGN:
        cur += ALIGN - (cur % ALIGN)
    offs = []
    for b in blobs:
        offs.append(cur)
        cur += len(b)
        if cur % ALIGN:
            cur += ALIGN - (cur % ALIGN)
    hdr = bytearray(struct.pack('<I', n))
    for i, nm in enumerate(names):
        hdr += nm.encode('latin1')[:56].ljust(56, b'\x00')
        hdr += struct.pack('<II', offs[i], len(blobs[i]))
    body = bytearray()
    pos = hdr_len
    for i, b in enumerate(blobs):
        pad = offs[i] - pos
        assert pad >= 0
        body += b'\x00' * pad
        body += b
        pos = offs[i] + len(b)
    return bytes(hdr) + bytes(body)

orig_font = open(os.path.join(BACK, 'font.lmp'), 'rb').read()
ents, cnt = parse_lmp(orig_font)
names = [e[0] for e in ents]
blobs = []
for nm, off, size in ents:
    if nm == 'gamefonta.fnt':
        blobs.append(open(os.path.join(ANA, 'gamefonta_v10.fnt'), 'rb').read())
        print('REPLACE gamefonta -> v10')
    else:
        blobs.append(orig_font[off:off + size])
new = build(names, blobs)
open(os.path.join(RES, 'font.lmp'), 'wb').write(new)
print(f'font.lmp: {len(orig_font)} -> {len(new)}')

# frontend.lmp original
front = open(os.path.join(BACK, 'frontend.lmp'), 'rb').read()
open(os.path.join(RES, 'frontend.lmp'), 'wb').write(front)
print('frontend.lmp: original', len(front))
print('DONE v10')