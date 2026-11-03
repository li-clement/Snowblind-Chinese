#!/usr/bin/env python3
# uni_bytes.py - precise per-entry layout diff: original vs rebuilt gtext.uni
import struct, os

BASE = r'E:\Game\ps5\iso'
RES  = os.path.join(BASE, "[XBOX].Baldur's.Gate.Dark.Alliance.[USA]", 'res')
BK   = os.path.join(BASE, 'backup_original')

def get_uni(path, ent):
    b = open(path, 'rb').read()
    cnt = struct.unpack_from('<I', b, 0)[0]
    for i in range(cnt):
        p = 4 + i * 64
        nm = b[p:p + 56].split(b'\x00', 1)[0].decode('latin1')
        off, size = struct.unpack_from('<II', b, p + 56)
        if nm == ent:
            return b[off:off + size]
    return None

def scan(u, limit=6):
    """scan entries, recording key len, text bytes len, and the exact tail bytes"""
    out = []
    pos = 0
    while pos < len(u) and len(out) < limit:
        k0 = u.find(b'\x00', pos)
        if k0 < 0 or k0 == pos:
            out.append(('BREAK_AT', pos))
            break
        key = u[pos:k0]
        pad = 1 if len(key) % 2 == 0 else 0
        t0 = k0 + 1 + pad
        t1 = t0
        while t1 + 1 < len(u):
            if u[t1] == 0 and u[t1 + 1] == 0:
                break
            t1 += 2
        text = u[t0:t1]
        tail = u[t1:t1 + 6]
        out.append((key.decode('latin1', 'replace'), len(text), tail.hex()))
        pos = t1 + 2
    return out

for label, path, ent in [('ORIG', os.path.join(BK, 'gtext.lmp'), 'gtext.uni'),
                          ('NEW ', os.path.join(RES, 'gtext.lmp'), 'gtext.uni')]:
    u = get_uni(path, ent)
    print(f"== {label} {ent}: {len(u)} bytes")
    for r in scan(u):
        print('   ', r)
    print()

# tail of file
for label, path, ent in [('ORIG', os.path.join(BK, 'gtext.lmp'), 'gtext.uni'),
                          ('NEW ', os.path.join(RES, 'gtext.lmp'), 'gtext.uni')]:
    u = get_uni(path, ent)
    print(f"{label} last 32 bytes: {u[-32:].hex()}")