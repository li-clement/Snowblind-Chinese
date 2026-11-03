#!/usr/bin/env python3
# uni_head.py - dump original uni file head + structure; compare original vs rebuilt gtext.uni
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

def dump_uni(u, label):
    print(f"== {label}: {len(u)} bytes")
    print(f"   head16: {u[:16].hex()}")
    # first 3 keys
    pos = 0
    for k in range(3):
        k0 = u.find(b'\x00', pos)
        if k0 < 0 or k0 == pos:
            print(f"   entry{k}: break at pos {pos} (k0={k0})")
            return pos, k
        key = u[pos:k0]
        pad = 1 if len(key) % 2 == 0 else 0
        t0 = k0 + 1 + pad
        t1 = t0
        while t1 + 1 < len(u):
            if u[t1] == 0 and u[t1 + 1] == 0:
                break
            t1 += 2
        txt = u[t0:t1].decode('utf-16-le', 'replace')
        print(f"   entry{k}: key={key[:20]!r} keylen={len(key)} pad={pad} textlen={len(txt)} text={txt[:24]!r}")
        pos = t1 + 2
    return pos, 3

orig = get_uni(os.path.join(BK, 'gtext.lmp'), 'gtext.uni')
new  = get_uni(os.path.join(RES, 'gtext.lmp'), 'gtext.uni')
if orig:
    dump_uni(orig, 'ORIGINAL gtext.uni')
if new:
    dump_uni(new, 'REBUILT gtext.uni')

# count entries in original
def count_entries(u):
    n = 0
    pos = 0
    while pos < len(u):
        k0 = u.find(b'\x00', pos)
        if k0 < 0 or k0 == pos:
            break
        n += 1
        key = u[pos:k0]
        pad = 1 if len(key) % 2 == 0 else 0
        t0 = k0 + 1 + pad
        t1 = t0
        while t1 + 1 < len(u):
            if u[t1] == 0 and u[t1 + 1] == 0:
                break
            t1 += 2
        pos = t1 + 2
    return n

if orig:
    print(f"original entries: {count_entries(orig)}")
if new:
    print(f"rebuilt entries: {count_entries(new)}")

# which keys does orig have but zh translation lacks? and vice versa
import json
TR = os.path.join(BASE, 'translation')
merged = {}
for f in os.listdir(TR):
    if f.startswith('zh_gtext'):
        with open(os.path.join(TR, f), encoding='utf-8') as fh:
            merged.update(json.load(fh))
print(f"zh_gtext keys: {len(merged)}")

def key_list(u):
    keys = []
    pos = 0
    while pos < len(u):
        k0 = u.find(b'\x00', pos)
        if k0 < 0 or k0 == pos:
            break
        key = u[pos:k0].decode('latin1', 'replace')
        keys.append(key)
        pad = 1 if len(key.encode('latin1')) % 2 == 0 else 0
        t0 = k0 + 1 + pad
        t1 = t0
        while t1 + 1 < len(u):
            if u[t1] == 0 and u[t1 + 1] == 0:
                break
            t1 += 2
        pos = t1 + 2
    return keys

if orig:
    ok = key_list(orig)
    miss = [k for k in ok if k not in merged]
    extra = [k for k in merged if k not in ok]
    print(f"original keys: {len(ok)}, missing in zh: {len(miss)} {miss[:20]}")
    print(f"zh keys not in original: {len(extra)} {extra[:20]}")