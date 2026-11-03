import struct, os
res = os.path.join(r"E:\Game\ps5\iso", "[XBOX].Baldur's.Gate.Dark.Alliance.[USA]", 'res')

def parse_lmp(b):
    cnt = struct.unpack_from('<I', b, 0)[0]
    out = []
    for i in range(min(cnt, 3000)):
        p = 4 + i*64
        nm = b[p:p+56].split(b'\0', 1)[0].decode('latin1')
        off, size = struct.unpack_from('<II', b, p+56)
        out.append((nm, off, size))
    return out, cnt

for lmp in ['font.lmp', 'frontend.lmp']:
    p_cur = os.path.join(res, lmp)
    p_orig = os.path.join(r'E:\Game\ps5\iso\backup_original', lmp)
    cur, _ = parse_lmp(open(p_cur, 'rb').read())
    orig, _ = parse_lmp(open(p_orig, 'rb').read())
    cur_names = [n for n, _, _ in cur]
    orig_names = [n for n, _, _ in orig]
    print(f'== {lmp} ==')
    print(f'  current ({len(cur)}): {cur_names}')
    print(f'  original({len(orig)}): {orig_names}')
    print(f'  current sorted? {cur_names == sorted(cur_names)}')
    print(f'  order preserved? {cur_names == orig_names}')