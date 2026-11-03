# swap v8 fonts into font.lmp + frontend.lmp, then pack ISO
import struct, os, subprocess

BASE = r'E:\Game\ps5\iso'
RES = os.path.join(BASE, "[XBOX].Baldur's.Gate.Dark.Alliance.[USA]", 'res')
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

def build_lmp(names, blobs):
    n = len(names)
    hdr = bytearray(struct.pack('<I', n))
    cur = 4 + n * 64
    offs = []
    for b in blobs:
        offs.append(cur)
        cur += len(b)
    for i, nm in enumerate(names):
        hdr += nm.encode('latin1')[:56].ljust(56, b'\x00')
        hdr += struct.pack('<II', offs[i], len(blobs[i]))
    return bytes(hdr) + b''.join(blobs)

for lmp, mp in targets.items():
    p = os.path.join(RES, lmp)
    old = open(p, 'rb').read()
    ents, cnt = parse_lmp(old)
    names, blobs = [], []
    for nm, off, size in ents:
        if nm in mp:
            v8 = os.path.join(ANA, mp[nm])
            if not os.path.exists(v8):
                raise SystemExit(f'!! missing {v8}')
            blobs.append(open(v8, 'rb').read())
            print(f'  {lmp}: {nm} <- {mp[nm]}')
        else:
            blobs.append(old[off:off + size])
        names.append(nm)
    new = build_lmp(names, blobs)
    open(p, 'wb').write(new)
    print(f'{lmp}: {len(old)} -> {len(new)}')

print('DONE swap')