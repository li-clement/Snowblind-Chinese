#!/usr/bin/env python3
import struct, os
base = r'E:\Game\ps5\iso'
res = os.path.join(base, "[XBOX].Baldur's.Gate.Dark.Alliance.[USA]", 'res')

def parse_lmp(data):
    if len(data) < 4:
        return []
    cnt = struct.unpack_from('<I', data, 0)[0]
    out = []
    for i in range(min(cnt, 3000)):
        p = 4 + i * 64
        nm = data[p:p + 56].split(b'\x00', 1)[0].decode('ascii', 'replace')
        off, size = struct.unpack_from('<II', data, p + 56)
        out.append((nm, off, size))
    return out

def parse_gob(data):
    out = []
    pos = 0
    while pos + 40 <= len(data):
        nm = data[pos:pos + 32].split(b'\x00', 1)[0].decode('ascii', 'replace')
        off, size = struct.unpack_from('<II', data, pos + 32)
        if nm == '' or off + size > len(data) or size == 0:
            break
        out.append((nm, off, size))
        pos += 40
    return out

for fn in ['font.lmp', 'dialogj.lmp', 'config.lmp', 'langmenu.lmp', 'start.lmp']:
    p = os.path.join(res, fn)
    print(f'== {fn}: exists={os.path.exists(p)}')
    if os.path.exists(p):
        b = open(p, 'rb').read()
        print(f'   size={len(b)}')
        ents = parse_lmp(b)
        if not ents:
            ents = parse_gob(b)
        for nm, off, size in ents[:40]:
            print(f'   {nm} off={off} size={size}')
        if len(ents) > 40:
            print(f'   ... and {len(ents)-40} more')
        if not ents:
            print('   no lmp/gob structure, first bytes:', b[:16].hex())