# v9 rebuild (fixed): start from BACKUP original lmps, replace fonts with v8 bodies,
# recompute offsets with recursive 0x80 alignment relative to FILE START.
import struct, os

BASE = r'E:\Game\ps5\iso'
RES = os.path.join(BASE, "[XBOX].Baldur's.Gate.Dark.Alliance.[USA]", 'res')
BACK = os.path.join(BASE, 'backup_original')
ANA = os.path.join(BASE, 'analysis')

targets = {
    'font.lmp':     {'gamefonta.fnt': 'gamefonta_v8.fnt', 'gamefontmed.fnt': 'gamefontmed_v8.fnt', 'gamefontsmall.fnt': 'gamefontsmall_v8.fnt'},
    'frontend.lmp': {'bigfont.fnt': 'bigfont_v8.fnt', 'creditfont.fnt': 'creditfont_v8.fnt', 'gamefontsmall.fnt': 'gamefontsmall_v8.fnt'},
}

def parse_lmp(b):
    cnt = struct.unpack_from('<I', b, 0)[0]
    out = []
    for i in range(cnt):
        p = 4 + i * 64
        nm = b[p:p + 56].split(b'\x00', 1)[0].decode('latin1')
        off, size = struct.unpack_from('<II', b, p + 56)
        out.append([nm, off, size])
    return out, cnt

def build(names, blobs, align=0x80):
    n = len(names)
    hdr_len = 4 + n * 64                       # 0xC4 for 3, 0x604 for 24
    # file layout: header (hdr_len bytes) then blobs at aligned offsets counted from file start
    cur = hdr_len
    if cur % align:
        cur += align - (cur % align)
    offs = []
    for b in blobs:
        offs.append(cur)
        cur += len(b)
        if cur % align:
            cur += align - (cur % align)
    hdr = bytearray(struct.pack('<I', n))
    for i, nm in enumerate(names):
        hdr += nm.encode('latin1')[:56].ljust(56, b'\x00')
        hdr += struct.pack('<II', offs[i], len(blobs[i]))
    # body: from hdr_len to end; pad so each blob lands exactly at offs[i]
    body = bytearray()
    pos = hdr_len
    for i, b in enumerate(blobs):
        pad = offs[i] - pos
        assert pad >= 0, f'overlap at {i}'
        body += b'\x00' * pad
        body += b
        pos = offs[i] + len(b)
    return bytes(hdr) + bytes(body)

for lmp, mp in targets.items():
    orig = open(os.path.join(BACK, lmp), 'rb').read()
    ents, cnt = parse_lmp(orig)
    names, blobs = [], []
    for nm, off, size in ents:
        if nm in mp:
            src = os.path.join(ANA, mp[nm])
            blobs.append(open(src, 'rb').read())
            print(f'  {lmp}: {nm} <- {mp[nm]} ({len(blobs[-1])}B)')
        else:
            blobs.append(orig[off:off + size])
        names.append(nm)
    new = build(names, blobs)
    open(os.path.join(RES, lmp), 'wb').write(new)
    print(f'{lmp}: orig {len(orig)} -> new {len(new)}')

print('DONE (fixed, from backup)')