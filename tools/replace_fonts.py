#!/usr/bin/env python3
# replace_fonts.py - swap font.fnt entries inside font.lmp / frontend.lmp with CJK build
import struct, os, shutil

BASE = r'E:\Game\ps5\iso'
RES  = os.path.join(BASE, "[XBOX].Baldur's.Gate.Dark.Alliance.[USA]", 'res')
FONT = r'E:\Game\ps5\iso\analysis\font_test_px.fnt'

def parse_lmp(data):
    cnt = struct.unpack_from('<I', data, 0)[0]
    out = []
    for i in range(min(cnt, 3000)):
        p = 4 + i * 64
        nm = data[p:p + 56].split(b'\x00', 1)[0].decode('ascii', 'replace')
        off, size = struct.unpack_from('<II', data, p + 56)
        out.append([nm, off, size])
    return out

def build_lmp(names, blobs):
    n = len(names)
    hdr = bytearray(struct.pack('<I', n))
    cur = 4 + n * 64
    offs = []
    for b in blobs:
        offs.append(cur)
        cur += len(b)
    for i, nm in enumerate(names):
        nb = nm.encode('ascii')[:56]
        hdr += nb.ljust(56, b'\x00')
        hdr += struct.pack('<II', offs[i], len(blobs[i]))
    return bytes(hdr) + b''.join(blobs)

zh_font = open(FONT, 'rb').read()
print(f"zh font: {len(zh_font)} bytes")

for fn in ['font.lmp', 'frontend.lmp']:
    p = os.path.join(RES, fn)
    old = open(p, 'rb').read()
    ents = parse_lmp(old)
    names, blobs = [], []
    changed = []
    for nm, off, size in ents:
        if nm.lower().endswith('.fnt'):
            blobs.append(zh_font)
            changed.append(nm)
        else:
            blobs.append(old[off:off + size])
        names.append(nm)
    new = build_lmp(names, blobs)
    open(p, 'wb').write(new)
    print(f"{fn}: {len(old)} -> {len(new)} bytes; replaced {changed}")

print("DONE")