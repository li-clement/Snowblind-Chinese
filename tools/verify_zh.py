#!/usr/bin/env python3
# verify_zh.py - verify patched .uni content: parse rebuilt gtext.lmp + gobs, check zh entries
import os, struct, sys

BASE = r'E:\Game\ps5\iso'
RES  = os.path.join(BASE, "[XBOX].Baldur's.Gate.Dark.Alliance.[USA]", 'res')

def parse_uni(data):
    items = []
    pos, n = 0, len(data)
    while pos + 4 < n:
        kstart = pos
        while pos < n and data[pos] != 0:
            pos += 1
        if pos >= n:
            break
        key = data[kstart:pos].decode('ascii', 'replace')
        if key == '':
            break
        pos += 1
        if pos % 2 != 0:
            pos += 1
        tstart = pos
        while pos + 1 < n and not (data[pos] == 0 and data[pos + 1] == 0):
            pos += 2
        txt = data[tstart:pos].decode('utf-16-le', 'replace')
        items.append([key, txt])
        pos = pos + 2
    return items

def parse_lmp(data):
    if len(data) < 4:
        return []
    cnt = struct.unpack_from('<I', data, 0)[0]
    if cnt < 1 or cnt > 4000 or 4 + cnt * 64 > len(data):
        return []
    out = []
    for i in range(cnt):
        p = 4 + i * 64
        nm = data[p:p + 56].split(b'\x00', 1)[0].decode('ascii', 'replace')
        off, size = struct.unpack_from('<II', data, p + 56)
        out.append([nm, off, size])
    return out

def parse_gob(data):
    out = []
    pos = 0
    while pos + 40 <= len(data):
        nm = data[pos:pos + 32].split(b'\x00', 1)[0].decode('ascii', 'replace')
        off, size = struct.unpack_from('<II', data, pos + 32)
        if nm == '' or off + size > len(data) or size == 0:
            break
        out.append([nm, off, size])
        pos += 40
    return out

def uni_stats(key, txts):
    zh = sum(1 for t in txts if any('\u4e00' <= ch <= '\u9fff' for ch in t))
    return f"{key}: {len(txts)} entries, {zh} with CJK"

# ---- gtext.lmp ----
gtext = open(os.path.join(RES, 'gtext.lmp'), 'rb').read()
ents = parse_lmp(gtext)
uni_all = []
for nm, off, size in ents:
    if nm == 'gtext.uni':
        u = parse_uni(gtext[off:off + size])
        uni_all = u
        print("gtext.uni:", len(u), "entries")
# spot checks
keymap = dict()
for k, t in uni_all:
    keymap.setdefault(k, t)
for probe in ['EnterGate', 'enterGate', 'Scimitar', 'scimitar_name', 'XMore', 'MemcardDeleteSlot']:
    if probe in keymap:
        print(f"  {probe} = {keymap[probe][:40]!r}")
# count all-CJK-English mixed
nonzh = [k for k, t in keymap.items() if not any('\u4e00' <= ch <= '\u9fff' for ch in t)]
print("  keys without CJK:", len(nonzh), nonzh[:20])

# ---- gobs ----
print()
for g in sorted(os.listdir(RES)):
    if not g.lower().endswith('.gob'):
        continue
    gb = open(os.path.join(RES, g), 'rb').read()
    gobEnts = parse_gob(gb)
    for nm, off, size in gobEnts:
        if not nm.endswith('.lmp'):
            continue
        lmp = gb[off:off + size]
        for lnm, loff, lsz in parse_lmp(lmp):
            if lnm.endswith('.uni') and '_' not in lnm:
                u = parse_uni(lmp[loff:loff + lsz])
                stats = uni_stats(f"{g}/{lnm}", [t for _k, t in u])
                print(stats)
print("\nVERIFY DONE")