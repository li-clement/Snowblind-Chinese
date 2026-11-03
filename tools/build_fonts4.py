#!/usr/bin/env python3
# build_fonts4.py - swap prebuilt *_v4.fnt files into resource lmp files
import struct, os

BASE = r'E:\Game\ps5\iso'
RES  = os.path.join(BASE, "[XBOX].Baldur's.Gate.Dark.Alliance.[USA]", 'res')
ANA  = os.path.join(BASE, 'analysis')

fonts = {
    'font.lmp':      ['gamefonta.fnt', 'gamefontmed.fnt', 'gamefontsmall.fnt'],
    'frontend.lmp':  ['bigfont.fnt', 'creditfont.fnt', 'gamefontsmall.fnt'],
}

def parse_lmp(b):
    cnt = struct.unpack_from('<I', b, 0)[0]
    out = []
    for i in range(min(cnt, 3000)):
        p = 4 + i * 64
        nm = b[p:p + 56].split(b'\x00', 1)[0].decode('latin1')
        off, size = struct.unpack_from('<II', b, p + 56)
        out.append([nm, off, size])
    return out, cnt

def build_lmp(names, blobs):
    n = len(names)
    hdr = bytearray(struct.pack('<I', n))
    cur = 4 + n * 64
    offs = []
    for b in blobs:
        offs.append(cur)
        cur += len(b)
    for i, nm in enumerate(names):
        nb = nm.encode('latin1')[:56]
        hdr += nb.ljust(56, b'\x00')
        hdr += struct.pack('<II', offs[i], len(blobs[i]))
    return bytes(hdr) + b''.join(blobs)

# verify all v4 files exist
for lmp, fns in fonts.items():
    for fn in fns:
        v4 = os.path.join(ANA, fn.replace('.fnt', '_v4.fnt'))
        if not os.path.exists(v4):
            raise SystemExit(f"!! missing {v4}")

for lmp, fns in fonts.items():
    p = os.path.join(RES, lmp)
    old = open(p, 'rb').read()
    ents, cnt = parse_lmp(old)
    names, blobs = [], []
    for nm, off, size in ents:
        v4 = None
        if nm in fns:
            v4 = os.path.join(ANA, nm.replace('.fnt', '_v5.fnt'))
        if v4 and os.path.exists(v4):
            blobs.append(open(v4, 'rb').read())
            print(f"  {lmp}: replace {nm} <- {os.path.basename(v4)}")
        else:
            blobs.append(old[off:off + size])
        names.append(nm)
    new = build_lmp(names, blobs)
    open(p, 'wb').write(new)
    print(f"{lmp}: {len(old)} -> {len(new)}")
print("DONE")