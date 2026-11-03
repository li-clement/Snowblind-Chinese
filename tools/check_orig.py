#!/usr/bin/env python3
# check_orig.py - compare gtext.lmp among backup_original, pristine extract, and res
import os, hashlib, struct

BASE = r'E:\Game\ps5\iso'
RES  = os.path.join(BASE, "[XBOX].Baldur's.Gate.Dark.Alliance.[USA]", 'res')
BK   = os.path.join(BASE, 'backup_original')

pristine = None
for d in os.listdir(BASE):
    full = os.path.join(BASE, d)
    if os.path.isdir(full) and d.startswith('_restore_tmp') and 'XBOX' in d:
        cand = os.path.join(full, 'res')
        if os.path.isdir(cand):
            pristine = cand
            break
print("pristine:", pristine)

def md5(p):
    return hashlib.md5(open(p, 'rb').read()).hexdigest() if os.path.exists(p) else 'MISSING'

for fn in ['gtext.lmp', 'font.lmp', 'frontend.lmp', 'tavern.gob']:
    p_res = os.path.join(RES, fn)
    p_bk  = os.path.join(BK, fn)
    p_pr  = os.path.join(pristine, fn) if pristine else None
    print(f"{fn}:")
    print(f"   res:{md5(p_res)} sz={os.path.getsize(p_res) if os.path.exists(p_res) else 0}")
    print(f"   bk :{md5(p_bk)} sz={os.path.getsize(p_bk) if os.path.exists(p_bk) else 0}")
    if p_pr:
        print(f"   pr :{md5(p_pr)} sz={os.path.getsize(p_pr) if os.path.exists(p_pr) else 0}")
    if p_pr and os.path.exists(p_pr) and os.path.exists(p_bk):
        print(f"   bk==pr? {md5(p_bk)==md5(p_pr)}")

# head bytes of backup gtext.uni vs pristine gtext.uni
def uni_info(path):
    b = open(path, 'rb').read()
    cnt = struct.unpack_from('<I', b, 0)[0]
    out = []
    for i in range(min(cnt, 10)):
        p = 4 + i * 64
        nm = b[p:p + 56].split(b'\x00', 1)[0].decode('latin1')
        off, size = struct.unpack_from('<II', b, p + 56)
        head = b[off:off + 16]
        out.append((nm, off, size, head.hex(), head[:12]))
    return out

print("\nbackup gtext.lmp entries:")
for r in uni_info(os.path.join(BK, 'gtext.lmp')):
    print("  ", r)
if pristine:
    print("\npristine gtext.lmp entries:")
    for r in uni_info(os.path.join(pristine, 'gtext.lmp')):
        print("  ", r)