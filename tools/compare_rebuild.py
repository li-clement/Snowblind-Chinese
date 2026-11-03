#!/usr/bin/env python3
# compare_rebuild.py - byte/structural diff: rebuilt res/* vs backup_original/*
#   for lmp: entry list (name, off, size); for gob: same; diff non-uni entries byte-wise
import struct, os, sys

BASE = r'E:\Game\ps5\iso'
RES  = os.path.join(BASE, "[XBOX].Baldur's.Gate.Dark.Alliance.[USA]", 'res')
BK   = os.path.join(BASE, 'backup_original')

def parse_lmp(b):
    if len(b) < 4:
        return []
    cnt = struct.unpack_from('<I', b, 0)[0]
    out = []
    for i in range(cnt):
        p = 4 + i * 64
        if p + 60 > len(b):
            break
        nm = b[p:p + 56].split(b'\x00', 1)[0].decode('latin1')
        off, size = struct.unpack_from('<II', b, p + 56)
        if off + size > len(b):
            break
        out.append([nm, off, size, b[off:off + size]])
    return out, cnt

def parse_gob(b):
    out = []
    pos = 0
    while pos + 40 <= len(b):
        nm = b[pos:pos + 32].split(b'\x00', 1)[0].decode('latin1')
        off, size = struct.unpack_from('<II', b, pos + 32)
        if nm == '' or off + size > len(b) or size == 0:
            break
        out.append([nm, off, size, b[off:off + size]])
        pos += 40
    return out, pos

def compare(fn):
    p_new = os.path.join(RES, fn)
    p_old = os.path.join(BK, fn)
    if not (os.path.exists(p_new) and os.path.exists(p_old)):
        return None
    nb = open(p_new, 'rb').read()
    ob = open(p_old, 'rb').read()
    isgob = fn.endswith('.gob')
    (ne, ncnt) = (parse_gob(nb) if isgob else parse_lmp(nb))
    (oe, ocnt) = (parse_gob(ob) if isgob else parse_lmp(ob))
    issues = []
    if len(ne) != len(oe):
        issues.append(f"ENTRY COUNT {len(oe)}->{len(ne)}")
    for i in range(min(len(oe), len(ne))):
        on, oo, osz, od = oe[i]
        nn, no, nsz, nd = ne[i]
        if on != nn:
            issues.append(f"  [{i}] name {on!r}->{nn!r}")
            continue
        dorename = on.endswith('.uni')
        if oo != no:
            issues.append(f"  [{i}] {on} off {oo}->{no}")
        if osz != nsz:
            issues.append(f"  [{i}] {on} size {osz}->{nsz}")
        if not dorename:
            if od != nd:
                issues.append(f"  [{i}] {on} NON-UNI BYTES DIFFER (len {osz}->{nsz})")
        else:
            # uni content: structural check only (key order/dup patterns)
            okeys = parse_uni_keys(od)
            nkeys = parse_uni_keys(nd)
            if okeys is None or nkeys is None:
                issues.append(f"  [{i}] {on} uni parse fail")
            elif okeys != nkeys:
                k0 = next((j for j in range(min(len(okeys), len(nkeys))) if okeys[j] != nkeys[j]), None)
                issues.append(f"  [{i}] {on} KEY LIST DIFFERS at {k0}: {okeys[k0] if k0 is not None and k0 < len(okeys) else 'END'} vs {nkeys[k0] if k0 is not None and k0 < len(nkeys) else 'END'} (n={len(okeys)}->{len(nkeys)})")
    return (fn, len(oe), len(ne), issues)

def parse_uni_keys(b):
    keys = []
    pos = 0
    guard = 0
    while pos < len(b) and guard < 5000:
        guard += 1
        k0 = b.find(b'\x00', pos)
        if k0 < 0 or k0 == pos:
            return None
        key = b[pos:k0]
        try:
            ks = key.decode('latin1')
        except Exception:
            return None
        if len(key) % 2 == 0:
            k0 += 1
        t0 = k0 + 1
        t1 = t0
        while t1 + 1 < len(b):
            if b[t1] == 0 and b[t1 + 1] == 0:
                break
            t1 += 2
        keys.append(ks)
        pos = t1 + 2
    return keys

fn = sys.argv[1] if len(sys.argv) > 1 else None
targets = [fn] if fn else sorted(os.listdir(BK))
checked = 0
for f in targets:
    if not f.endswith(('.lmp', '.gob')):
        continue
    r = compare(f)
    if r and r[3]:
        print(f"== {r[0]}: {r[1]}->{r[2]} entries, {len(r[3])} issues")
        for x in r[3]:
            print(f"   {x}")
        checked += 1
print(f"\nchecked {checked} files with issues")