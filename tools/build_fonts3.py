#!/usr/bin/env python3
# build_fonts3.py - build conservative CJK fonts for all latin fnts, then swap into lmp files
import struct, os, sys, subprocess

BASE = r'E:\Game\ps5\iso'
RES  = os.path.join(BASE, "[XBOX].Baldur's.Gate.Dark.Alliance.[USA]", 'res')
ANA  = os.path.join(BASE, 'analysis')
PY   = r'C:\Users\Administrator\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe'
BUILD= os.path.join(BASE, 'tools', 'fnt_build3.py')

ANALYSIS = ANA
fonts = {
    'font.lmp':      ['gamefonta.fnt', 'gamefontmed.fnt', 'gamefontsmall.fnt'],
    'frontend.lmp':  ['bigfont.fnt', 'creditfont.fnt', 'gamefontsmall.fnt'],
}
# keep japfontbig0/japfontsmall0 untouched

def parse_lmp(b):
    cnt = struct.unpack_from('<I', b, 0)[0]
    out = []
    for i in range(min(cnt, 3000)):
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
        nb = nm.encode('latin1')[:56]
        hdr += nb.ljust(56, b'\x00')
        hdr += struct.pack('<II', offs[i], len(blobs[i]))
    return bytes(hdr) + b''.join(blobs)

# 1) build each font once
built = {}
for lmp, fns in fonts.items():
    for fn in fns:
        if fn in built:
            continue
        src = os.path.join(ANALYSIS, fn)
        dst = os.path.join(ANALYSIS, fn.replace('.fnt', '_zh.fnt'))
        if not os.path.exists(src):
            print(f"!! missing {src}")
            continue
        r = subprocess.run([PY, BUILD, src, dst, '16'], capture_output=True, text=True)
        print(f"build {fn}: rc={r.returncode} {r.stdout.strip().splitlines()[-1] if r.stdout.strip() else r.stderr.strip()[-200:]}")
        if r.returncode == 0:
            built[fn] = dst
        else:
            print("   STDERR:", r.stderr[-500:])

# 2) swap into lmp files
for lmp, fns in fonts.items():
    p = os.path.join(RES, lmp)
    old = open(p, 'rb').read()
    ents, cnt = parse_lmp(old)
    names, blobs = [], []
    for nm, off, size in ents:
        if nm in built:
            blobs.append(open(built[nm], 'rb').read())
            print(f"  {lmp}: replacing {nm}")
        else:
            blobs.append(old[off:off + size])
        names.append(nm)
    new = build_lmp(names, blobs)
    open(p, 'wb').write(new)
    print(f"{lmp}: {len(old)} -> {len(new)}")
print("DONE")