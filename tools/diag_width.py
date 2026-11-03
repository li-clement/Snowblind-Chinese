#!/usr/bin/env python3
# Diagnostic: crop v15 fonts' atlas width 2048 -> 1024 (keep left columns),
# rebuild font.lmp so we can test whether atw=2048 alone causes the black screen.
import struct, os, sys

ALIGN = 0x80
def aligned(x): return (x + ALIGN - 1) & ~(ALIGN - 1)

def crop_font(fb, new_atw):
    cnt, hgt = struct.unpack_from('<HH', fb, 0)
    nsect, magic, oSec, oBmp = struct.unpack_from('<IIII', fb, 4)
    atw, ath = struct.unpack_from('<HH', fb, oBmp)
    start = oBmp + 1080
    old = fb[start:start + atw * ath]
    new = bytearray()
    for yy in range(ath):
        new += old[yy * atw: yy * atw + new_atw]
    out = bytearray(fb[:start]) + new
    struct.pack_into('<HH', out, oBmp, new_atw, ath)
    # any record referencing x >= new_atw is now invalid; clamp x1 to new_atw so
    # sampling never reads past row end (glyphs there become blank, harmless for test)
    REC = 0x214
    i = 0
    while True:
        p = REC + i * 16
        if p + 16 > oSec: break
        code, x0, x1, y0, y1, f5, adv, kern = struct.unpack_from('<8H', out, p)
        if code == 0xFFFF and x0 == 0xFFFF: break
        if x1 > new_atw or x0 >= new_atw:
            # blank it: point to a zero rect at (0,0,0,0) with adv kept
            struct.pack_into('<8H', out, p, code, 0, 0, 0, 0, f5, adv, kern)
        i += 1
    return bytes(out)

def rebuild_lmp(src, dst, new_atw):
    b = open(src, 'rb').read()
    cnt = struct.unpack_from('<I', b, 0)[0]
    entries = []
    for i in range(cnt):
        p = 4 + i * 64
        n = b[p:p + 56]
        off, size = struct.unpack_from('<II', b, p + 56)
        name = n.split(b'\x00', 1)[0].decode('latin1')
        pl = b[off:off + size]
        if name.endswith('.fnt'):
            pl = crop_font(pl, new_atw)
        entries.append((n, pl))
    out = bytearray(struct.pack('<I', cnt))
    hdr_end = 4 + cnt * 64
    cur = aligned(hdr_end)
    recs = []
    for n, pl in entries:
        recs.append((cur, len(pl)))
        cur += len(pl); cur = aligned(cur)
    # header block
    out += b''  # placeholder; rebuild fully
    buf = bytearray(struct.pack('<I', cnt))
    for (n, _), (off, size) in zip(entries, recs):
        buf += n + struct.pack('<II', off, size)
    body = bytearray(buf[:aligned(len(buf))])
    for (n, pl), (off, size) in zip(entries, recs):
        while len(body) < off: body.append(0)
        body[off:off + len(pl)] = pl
    open(dst, 'wb').write(bytes(body))
    print(f'{os.path.basename(dst)}: {len(body)} bytes')

if __name__ == '__main__':
    sys.exit("use via test harness")
