#!/usr/bin/env python3
# patch_inplace.py - in-place .uni replacement inside .lmp/.gob containers
#   Layout of target files stays byte-identical EXCEPT:
#     - each .uni entry's payload is replaced by the rebuilt (zh) payload
#     - the entry's size field is updated (new size must be <= old size)
#   This preserves the original 2048/512 alignment and all binary blocks.
import struct, os, json

BASE = r'E:\Game\ps5\iso'
RES  = os.path.join(BASE, "[XBOX].Baldur's.Gate.Dark.Alliance.[USA]", 'res')
TR   = os.path.join(BASE, 'translation')
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

def parse_uni(b):
    """returns list of (key, text) preserving duplicate keys and order"""
    out = []
    pos = 0
    while pos < len(b):
        k0 = b.find(b'\x00', pos)
        if k0 < 0 or k0 == pos:
            break
        key = b[pos:k0].decode('latin1', 'replace')
        if len(key) % 2 == 0:
            k0 += 1
        t0 = k0 + 1
        t1 = t0
        while t1 + 1 < len(b):
            if b[t1] == 0 and b[t1 + 1] == 0:
                break
            t1 += 2
        text = b[t0:t1].decode('utf-16-le', 'replace')
        out.append((key, text))
        pos = t1 + 2
    return out

def build_uni(pairs):
    """rebuild uni from (key, text) pairs preserving duplicates/order; follow original padding"""
    out = bytearray()
    for key, text in pairs:
        kb = key.encode('latin1', 'replace')
        out += kb
        out += b'\x00'
        if len(kb) % 2 == 0:
            out += b'\x00'
        out += text.encode('utf-16-le')
        out += b'\x00\x00'
    return bytes(out)

def patch_container(path, uni_map):
    """in-place patch: returns (new_bytes, [(name, old, new)]) or None on growth"""
    b = open(path, 'rb').read()
    isgob = path.lower().endswith('.gob')
    if isgob:
        ents = parse_gob(b)
        n = len(ents)
        hlen = n * 40
    else:
        ents, n = parse_lmp(b)
        hlen = 4 + n * 64

    mods = []
    newblob = bytearray(b)
    for nm, off, size in ents:
        if nm.lower().endswith('.uni'):
            old = b[off:off + size]
            pairs = parse_uni(old)
            newpairs = [(k, uni_map.get(k, t)) for k, t in pairs]
            new = build_uni(newpairs)
            if len(new) > len(old):
                return None, f"UNI {nm} grows {len(old)}->{len(new)}"
            newblob[off:off + len(new)] = new
            # update dir size
            if isgob:
                for i in range(n):
                    if ents[i][0] == nm:
                        struct.pack_into('<I', newblob, i * 40 + 36, len(new))
            else:
                for i in range(n):
                    if ents[i][0] == nm:
                        struct.pack_into('<I', newblob, 4 + i * 64 + 60, len(new))
            mods.append((nm, len(old), len(new)))
        elif nm.lower().endswith('.lmp') and isgob:
            # nested lmp: patch its own uni entries in place
            inner = b[off:off + size]
            ients, icnt = parse_lmp(inner)
            innerblob = bytearray(inner)
            for inm, ioff, isz in ients:
                if inm.lower().endswith('.uni'):
                    iold = inner[ioff:ioff + isz]
                    pairs = parse_uni(iold)
                    newpairs = [(k, uni_map.get(k, t)) for k, t in pairs]
                    inew = build_uni(newpairs)
                    if len(inew) > len(iold):
                        return None, f"UNI {nm}/{inm} grows {len(iold)}->{len(inew)}"
                    innerblob[ioff:ioff + len(inew)] = inew
                    for i in range(icnt):
                        if ients[i][0] == inm:
                            struct.pack_into('<I', innerblob, 4 + i * 64 + 60, len(inew))
                    mods.append((f"{nm}/{inm}", len(iold), len(inew)))
            if mods:
                newbytes = bytes(innerblob)
                if len(newbytes) > size:
                    return None, f"inner lmp {nm} grows"
                newblob[off:off + len(newbytes)] = newbytes
                if isgob:
                    for i in range(n):
                        if ents[i][0] == nm:
                            struct.pack_into('<I', newblob, i * 40 + 36, len(newbytes))
    if not mods:
        return None, "no uni entries"
    return bytes(newblob), None

def main():
    # load translations
    files = ['zh_act1.uni.json', 'zh_act2.uni.json', 'zh_act3.uni.json', 'zh_tavern.uni.json',
             'zh_bthrone_cut.uni.json', 'zh_cuttown_cut.uni.json', 'zh_xantam.uni.json',
             'zh_sewer1_cut.uni.json', 'zh_csewer1_cut.uni.json', 'zh_towert_cut.uni.json',
             'zh_gtext_part1.uni.json', 'zh_gtext_part2.uni.json']
    merged = {}
    for f in files:
        p = os.path.join(TR, f)
        with open(p, encoding='utf-8') as fh:
            obj = json.load(fh)
        for k, v in obj.items():
            merged[k] = v
    print(f"translation keys: {len(merged)}")

    # targets: gtext.lmp + all gobs containing uni (same set as before)
    targets = ['gtext.lmp',
               'bthrone.gob', 'chekeep2.gob', 'crypt1.gob', 'crypt2.gob', 'csewer1.gob',
               'cuttown.gob', 'mine3.gob', 'minecamp.gob', 'sewer1.gob', 'smlcave3.gob',
               'swamp1.gob', 'swamp2.gob', 'tavern.gob', 'temple1.gob', 'thieves2.gob',
               'towerh.gob', 'towert.gob']
    any_grow = False
    for t in targets:
        p = os.path.join(RES, t)
        if not os.path.exists(p):
            print(f"MISSING {t}")
            continue
        nb, err = patch_container(p, merged)
        if err:
            print(f"! {t}: {err}")
            any_grow = True
        else:
            open(p, 'wb').write(nb)
            print(f"patched {t}")
    if any_grow:
        print("*** SOME UNI GREW - need manual handling ***")
    else:
        print("ALL OK - in-place patch done, layout preserved")

if __name__ == '__main__':
    main()