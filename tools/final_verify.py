#!/usr/bin/env python3
# final_verify.py - extract fnt from patched lmp + re-verify zh text counts
import struct, os, sys

BASE = r'E:\Game\ps5\iso'
RES  = os.path.join(BASE, "[XBOX].Baldur's.Gate.Dark.Alliance.[USA]", 'res')

def parse_lmp(data):
    cnt = struct.unpack_from('<I', data, 0)[0]
    out = {}
    for i in range(min(cnt, 3000)):
        p = 4 + i * 64
        nm = data[p:p + 56].split(b'\x00', 1)[0].decode('ascii', 'replace')
        off, size = struct.unpack_from('<II', data, p + 56)
        out[nm] = (off, size)
    return out

def check_fnt(b):
    if len(b) < 20:
        return None
    cnt, hgt = struct.unpack_from('<HH', b, 0)
    nsect, magic, offSec, offBmp = struct.unpack_from('<IIII', b, 4)
    if offBmp + 1084 > len(b):
        return None
    atw, ath = struct.unpack_from('<HH', b, offBmp)
    ok = (len(b) == offBmp + 1080 + atw * ath)
    return (cnt, hgt, atw, ath, ok)

print("== font.lmp ==")
b = open(os.path.join(RES, 'font.lmp'), 'rb').read()
for nm, (off, size) in parse_lmp(b).items():
    if nm.endswith('.fnt'):
        r = check_fnt(b[off:off + size])
        print(f"  {nm}: size={size} -> {r}")

print("== frontend.lmp ==")
b = open(os.path.join(RES, 'frontend.lmp'), 'rb').read()
for nm, (off, size) in parse_lmp(b).items():
    if nm.endswith('.fnt'):
        r = check_fnt(b[off:off + size])
        print(f"  {nm}: size={size} -> {r}")

# zh text spot check: can patch_uni parse still? count CJK in gtext.uni
print("== gtext.lmp zh check ==")
b = open(os.path.join(RES, 'gtext.lmp'), 'rb').read()
ents = parse_lmp(b)
off, size = ents['gtext.uni']
uni = b[off:off + size]
# parse unis
pos = 0
n = 0
while pos < len(uni):
    k0 = uni.find(b'\x00', pos)
    if k0 < 0:
        break
    key = uni[pos:k0]
    if len(key) % 2 == 0:
        k0 += 1
    # text runs to 00 00
    t0 = k0 + 1
    t1 = t0
    while t1 + 1 < len(uni):
        if uni[t1] == 0 and uni[t1 + 1] == 0:
            break
        t1 += 2
    text = uni[t0:t1].decode('utf-16-le', 'replace')
    if any('\u4e00' <= c <= '\u9fff' for c in text):
        n += 1
    pos = t1 + 2
print(f"  gtext.uni: {n} entries with CJK (expect ~902)")
print("DONE")