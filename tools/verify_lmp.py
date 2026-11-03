import struct, os
res = os.path.join(r"E:\Game\ps5\iso", "[XBOX].Baldur's.Gate.Dark.Alliance.[USA]", 'res')
def parse_lmp(b):
    cnt = struct.unpack_from('<I', b, 0)[0]
    out=[]
    for i in range(min(cnt,3000)):
        p=4+i*64
        nm=b[p:p+56].split(b'\0',1)[0].decode('latin1')
        off,size=struct.unpack_from('<II',b,p+56)
        out.append((nm,off,size))
    return cnt,out
for lmp in ['font.lmp','frontend.lmp']:
    p = os.path.join(res, lmp)
    b = open(p,'rb').read()
    cnt,ents = parse_lmp(b)
    print(f'{lmp}: size={len(b)} entries={cnt}')
    for nm,off,size in ents:
        if '.fnt' in nm:
            h = b[off:off+4]
            c2,h2 = struct.unpack_from('<HH', h, 0) if len(h)>=4 else (0,0)
            print(f'   {nm:<24} off={off:8} size={size:8} cnt={c2} hgt={h2}')