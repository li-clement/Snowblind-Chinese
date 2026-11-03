#!/usr/bin/env python3
# patch_uni.py - write back zh translations into .uni files, rebuild .lmp / .gob containers
# (Python port of the former patch_uni.ps1; case-sensitive key lookup, verbatim copy for untranslated)
import json, os, struct, glob

BASE   = r'E:\Game\ps5\iso'
RES    = os.path.join(BASE, '[XBOX].Baldur\'s.Gate.Dark.Alliance.[USA]', 'res')
TR     = os.path.join(BASE, 'translation')
BACKUP = os.path.join(BASE, 'backup_original')

ZH_FILES = ['zh_act1.uni.json', 'zh_act2.uni.json', 'zh_act3.uni.json', 'zh_tavern.uni.json',
            'zh_bthrone_cut.uni.json', 'zh_cuttown_cut.uni.json', 'zh_xantam.uni.json',
            'zh_sewer1_cut.uni.json', 'zh_csewer1_cut.uni.json', 'zh_towert_cut.uni.json']


def load_zhdict(path):
    with open(path, encoding='utf-8') as fh:
        obj = json.load(fh)
    return {k: str(v) for k, v in obj.items()}


def parse_uni(data):
    """parse .uni: ASCII key\\0 (+pad if key len even) + UTF-16LE text + 00 00.
    returns list of (key, text, start, end_excl, raw_bytes)"""
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
        end = pos + 2
        items.append([key, txt, kstart, end, bytes(data[kstart:end])])
        pos = end
    return items


def build_uni(key, text):
    kb = key.encode('ascii')
    out = bytearray(kb)
    out.append(0)
    if len(kb) % 2 == 0:
        out.append(0)
    out += text.encode('utf-16-le')
    out += b'\x00\x00'
    return bytes(out)


def patch_uni_blob(orig, zh):
    """rebuild a .uni blob: translated entries -> zh text, others copied verbatim.
    returns (new_bytes, n_entries, n_translated)"""
    items = parse_uni(orig)
    missing = []
    parts = []
    for key, txt, s, e, raw in items:
        if key in zh:
            parts.append(build_uni(key, zh[key]))
        else:
            parts.append(raw)
            missing.append(key)
    return b''.join(parts), len(items), len(parts) - len(missing), missing


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


def parse_lmp(data):
    """returns list of (name, off, size)"""
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


def main():
    os.makedirs(BACKUP, exist_ok=True)

    # ---- load zh dicts ----
    zhDicts = {}
    for jf in ZH_FILES:
        p = os.path.join(TR, jf)
        if os.path.exists(p):
            d = load_zhdict(p)
            name = jf[len('zh_'):-len('.json')]
            zhDicts[name] = d
            print(f"loaded {name}: {len(d)} keys")
    g1 = load_zhdict(os.path.join(TR, 'zh_gtext_part1.uni.json'))
    g2 = load_zhdict(os.path.join(TR, 'zh_gtext_part2.uni.json'))
    gm = dict(g1)
    gm.update(g2)
    zhDicts['gtext.uni'] = gm
    print(f"merged gtext.uni: {len(gm)} keys (part1 {len(g1)} + part2 {len(g2)})")

    # ---- Stage 1: backup (glob can't be used: '[' in dir name is a glob metachar) ----
    lmps = [os.path.join(RES, f) for f in os.listdir(RES) if f.lower().endswith('.lmp')]
    gobs = [os.path.join(dp, f) for dp, _dn, fn in os.walk(RES) for f in fn if f.lower().endswith('.gob')]
    nback = 0
    for f in lmps + gobs:
        dst = os.path.join(BACKUP, os.path.basename(f))
        if not os.path.exists(dst):
            import shutil
            shutil.copy2(f, dst)
            nback += 1
    print(f"\n== Stage 1: backed up {nback} files to {BACKUP} (of {len(lmps)+len(gobs)}) ==")

    # ---- Stage 2: rebuild gtext.lmp ----
    gtext_path = os.path.join(RES, 'gtext.lmp')
    gb = open(gtext_path, 'rb').read()
    ge = parse_lmp(gb) or parse_gob(gb)  # top-level containers: lmp format entry table
    names, blobs = [], []
    for nm, off, size in ge:
        orig = gb[off:off + size]
        if nm in zhDicts and nm.endswith('.uni'):
            nb, n_e, n_tr, missing = patch_uni_blob(orig, zhDicts[nm])
            print(f"  gtext.lmp/{nm}: {n_e} entries, {n_tr} translated, {len(missing)} missing keys kept EN")
            blobs.append(nb)
        else:
            blobs.append(orig)
        names.append(nm)
    newG = build_lmp(names, blobs)
    open(gtext_path, 'wb').write(newG)
    print(f"gtext.lmp rebuilt: {len(gb)} -> {len(newG)} bytes")

    # ---- Stage 3: rebuild .gob ----
    for gpath in gobs:
        gb = open(gpath, 'rb').read()
        gobEnts = parse_gob(gb)
        if not gobEnts:
            continue
        changed = []
        for nm, off, size in gobEnts:
            if not nm.endswith('.lmp'):
                continue
            lmpRaw = gb[off:off + size]
            lEnts = parse_lmp(lmpRaw)
            if not lEnts:
                continue
            hit = [e for e in lEnts if e[0] in zhDicts]
            if not hit:
                continue
            names, blobs = [], []
            for lnm, loff, lsz in lEnts:
                orig = lmpRaw[loff:loff + lsz]
                if lnm in zhDicts and lnm.endswith('.uni'):
                    nb, n_e, n_tr, missing = patch_uni_blob(orig, zhDicts[lnm])
                    if missing:
                        print(f"  WARN {gpath}/{lnm}: {len(missing)} keys missing from zh (kept EN): {missing[:5]}")
                    names.append(lnm)
                    blobs.append(nb)
                else:
                    names.append(lnm)
                    blobs.append(orig)
            changed.append([nm, build_lmp(names, blobs)])
        if not changed:
            continue
        names, blobs = [], []
        for nm, off, size in gobEnts:
            chg = [c for c in changed if c[0] == nm]
            if chg:
                blobs.append(chg[0][1])
            else:
                blobs.append(gb[off:off + size])
            names.append(nm)
        newGob = build_gob(names, blobs)
        open(gpath, 'wb').write(newGob)
        print(f"  rebuilt {os.path.basename(gpath)}: {len(changed)} changed lmps, {len(gb)} -> {len(newGob)} bytes")
    print("\nDONE")


def build_gob(names, blobs):
    n = len(names)
    hdr = bytearray()
    cur = n * 40
    offs = []
    for b in blobs:
        offs.append(cur)
        cur += len(b)
    for i, nm in enumerate(names):
        nb = nm.encode('ascii')[:32]
        hdr += nb.ljust(32, b'\x00')
        hdr += struct.pack('<II', offs[i], len(blobs[i]))
    return bytes(hdr) + b''.join(blobs)


if __name__ == '__main__':
    main()