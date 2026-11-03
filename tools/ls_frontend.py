#!/usr/bin/env python3
import struct, os
base = r'E:\Game\ps5\iso'
res = os.path.join(base, "[XBOX].Baldur's.Gate.Dark.Alliance.[USA]", 'res')

def parse_lmp(data):
    cnt = struct.unpack_from('<I', data, 0)[0]
    out = []
    for i in range(min(cnt, 3000)):
        p = 4 + i * 64
        nm = data[p:p + 56].split(b'\x00', 1)[0].decode('ascii', 'replace')
        off, size = struct.unpack_from('<II', data, p + 56)
        out.append((nm, off, size))
    return out

for fn in ['frontend.lmp', 'gtext.lmp']:
    p = os.path.join(res, fn)
    print(f'{fn}: exists={os.path.exists(p)}')
    if os.path.exists(p):
        b = open(p, 'rb').read()
        for nm, off, size in parse_lmp(b):
            mark = ' <-- FONT' if 'font' in nm.lower() else ''
            print(f'  {nm} off={off} size={size}{mark}')

bk = os.path.join(base, 'backup_original')
print('\nbackup_original contains:')
for f in sorted(os.listdir(bk)):
    print('  ', f)