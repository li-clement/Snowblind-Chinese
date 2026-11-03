import struct, shutil, sys
ALIGN=0x80
def aligned(x): return (x+ALIGN-1)&~(ALIGN-1)
def pad_ath(fb,new_ath):
    cnt,hgt=struct.unpack_from('<HH',fb,0); _,_,oSec,oBmp=struct.unpack_from('<IIII',fb,4)
    atw,ath=struct.unpack_from('<HH',fb,oBmp); start=oBmp+1080
    tail=len(fb)-(start+atw*ath)
    old=bytes(fb[start:start+atw*ath]); tailb=bytes(fb[start+atw*ath:])
    new=bytearray(atw*new_ath)
    for yy in range(ath): new[yy*atw:(yy+1)*atw]=old[yy*atw:(yy+1)*atw]
    out=bytearray(fb[:start])+new+tailb
    struct.pack_into('<HH',out,oBmp,atw,new_ath); return bytes(out)
def build(dst_dir,new_ath,src='font.lmp'):
    shutil.rmtree(dst_dir,ignore_errors=True)
    shutil.copytree("[XBOX].Baldur's.Gate.Dark.Alliance.[USA]",dst_dir)
    for nm in ('font.lmp','frontend.lmp'):
        b=open(f'_c14/res/{nm}','rb').read(); cnt=struct.unpack_from('<I',b,0)[0]; entries=[]
        for i in range(cnt):
            p=4+i*64; n=b[p:p+56]; off,size=struct.unpack_from('<II',b,p+56)
            name=n.split(b'\x00',1)[0].decode('latin1'); pl=b[off:off+size]
            if name.endswith('.fnt') and not name.startswith('jap'): pl=pad_ath(pl,new_ath)
            entries.append((n,pl))
        recs=[]; cur=aligned(4+cnt*64)
        for n,pl in entries: recs.append((cur,len(pl))); cur+=len(pl); cur=aligned(cur)
        buf=bytearray(struct.pack('<I',cnt))
        for (n,_),(o,s) in zip(entries,recs): buf+=n+struct.pack('<II',o,s)
        body=bytearray(buf[:aligned(len(buf))])
        for (n,pl),(o,s) in zip(entries,recs):
            while len(body)<o: body.append(0)
            body[o:o+len(pl)]=pl
        open(f'{dst_dir}/res/{nm}','wb').write(bytes(body))
if __name__=='__main__':
    build(sys.argv[1],int(sys.argv[2]))
