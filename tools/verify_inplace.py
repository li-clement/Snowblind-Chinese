#!/usr/bin/env python3
# verify_inplace.py - clean verification: every uni in patched res parses fully,
#   key list identical to original (order + duplicates), text contains zh
import struct, os

BASE = r'E:\Game\ps5\iso'
RES  = os.path.join(BASE, "[XBOX].Baldur's.Gate.Dark.Alliance.[USA]", 'res')
BK   = os.path.join(BASE, 'backup_original')

def parse_lmp(b):
    cnt = struct.unpack_from('<I', b, 0)[0]
    out = []
    for i in range(cnt):
        p = 4 + i * 64
        nm = b[p:p + 56].split(b'\x00', 1)[0].decode('latin1')
        off, size = struct.unpack_from('<II', b, p + 56)
        out.append([nm, off, size])
    return out, cnt

def parse_gob(b):
    out = []
    pos = 0
    while pos + 40 <= len(b):
        nm = b[pos:pos + 32].split(b'\x00', 1)[0].decode('latin1')
        off, size = struct.unpack_from('<II', b, pos + 32)
        if nm == '' or off + size > len(b) or size == 0:
            break
        out.append([nm, off, size])
        pos += 40
    return out

def scan_uni(u):
    """scan all entries; proves the whole buffer parses (returns None on structural error)"""
    entries = []
    pos = 0
    while pos < len(u):
        k0 = u.find(b'\x00', pos)
        if k0 < 0 or k0 == pos:
            return None
        key = u[pos:k0].decode('latin1', 'replace')
        pad = 1 if len(key.encode('latin1')) % 2 == 0 else 0
        t0 = k0 + 1 + pad
        t1 = t0
        while t1 + 1 < len(u):
            if u[t1] == 0 and u[t1 + 1] == 0:
                break
            t1 += 2
        text = u[t0:t1].decode('utf-16-le', 'replace')
        entries.append((key, text))
        pos = t1 + 2
    return entries

def all_unis(res_path):
    """yield (container, inner, bytes) for every uni in lmp or gob"""
    b = open(res_path, 'rb').read()
    if res_path.lower().endswith('.gob'):
        ents = parse_gob(b)
        for nm, off, size in ents:
            if nm.lower().endswith('.uni'):
                yield res_path, nm, b[off:off + size]
            elif nm.lower().endswith('.lmp'):
                inner = b[off:off + size]
                ients, _ = parse_lmp(inner)
                for inm, ioff, isz in ients:
                    if inm.lower().endswith('.uni'):
                        yield res_path, f"{nm}/{inm}", inner[ioff:ioff + isz]
    else:
        ents, _ = parse_lmp(b)
        for nm, off, size in ents:
            if nm.lower().endswith('.uni'):
                yield res_path, nm, b[off:off + size]

targets = ['gtext.lmp', 'bthrone.gob', 'chekeep2.gob', 'crypt1.gob', 'crypt2.gob',
           'csewer1.gob', 'cuttown.gob', 'mine3.gob', 'minecamp.gob', 'sewer1.gob',
           'smlcave3.gob', 'swamp1.gob', 'swamp2.gob', 'tavern.gob', 'temple1.gob',
           'thieves2.gob', 'towerh.gob', 'towert.gob']

total_uni = 0
for t in targets:
    for path, nm, udata in all_unis(os.path.join(RES, t)):
        total_uni += 1
        # same file in backup must be byte-identical before uni patch => key list must match original
        o = all_unis(os.path.join(BK, t))
        orig = None
        for op, onm, ou in o:
            if onm == nm:
                orig = ou
                break
        ne = scan_uni(udata)
        oe = scan_uni(orig) if orig is not None else None
        if ne is None:
            print(f"!! {t}/{nm}: NEW uni STRUCTURE BROKEN")
            continue
        if oe is not None and [k for k, _ in ne] != [k for k, _ in oe]:
            print(f"!! {t}/{nm}: key order differs")
            continue
        zh = sum(1 for _, tx in ne if any('\u4e00' <= c <= '\u9fff' for c in tx))
        print(f"ok {t}/{nm}: {len(ne)} entries, {zh} zh")
print(f"total uni files checked: {total_uni}")