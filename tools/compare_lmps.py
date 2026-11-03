import struct, os, glob
base = glob.glob(r"E:\Game\ps5\iso\[XBOX].Baldur's.Gate.Dark.Alliance.[USA]")[0]
res = os.path.join(base, 'res')
bak = os.path.join(base, 'backup_original')
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
    print('===== '+lmp+' =====')
    for label,d in [('RES',res),('ORIG',bak)]:
        p=os.path.join(d,lmp)
        if not os.path.exists(p): print(label+': MISSING'); continue
        b=open(p,'rb').read(); cnt,ents=parse_lmp(b)
        print(f'{label}: size={len(b)} entries={cnt}')
        for nm,off,size in ents: print(f'  {nm:<28} off={off:8} size={size:8}')
