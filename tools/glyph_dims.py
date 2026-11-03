import struct, os
ANA = r'E:\Game\ps5\iso\analysis'
res = r"E:\Game\ps5\iso\[XBOX].Baldur's.Gate.Dark.Alliance.[USA]\res"
backup = r'E:\Game\ps5\iso\backup_original'

def load_font(path):
    b = open(path, 'rb').read()
    cnt, hgt = struct.unpack_from('<HH', b, 0)
    nsect, magic, offSec, offBmp = struct.unpack_from('<IIII', b, 4)
    atw, ath = struct.unpack_from('<HH', b, offBmp)
    recStart = offSec - cnt*16
    recs = [struct.unpack_from('<8H', b, recStart+i*16) for i in range(cnt)]
    return dict(cnt=cnt, hgt=hgt, atw=atw, ath=ath, recs=recs, b=b, start=offBmp+1080)

def stats(f):
    ws, hs = [], []
    for v in f['recs']:
        c, f1, f2, f3, f4 = v[0], v[1], v[2], v[3], v[4]
        w = f2-f1; h = f4-f3
        if 0 < w < 200 and 0 < h < 200:
            ws.append(w); hs.append(h)
    return ws, hs

for lmp, fns in [('font.lmp', ['gamefonta.fnt','gamefontmed.fnt','gamefontsmall.fnt']),
                 ('frontend.lmp', ['bigfont.fnt','creditfont.fnt','gamefontsmall.fnt'])]:
    b = open(os.path.join(backup if os.path.exists(os.path.join(backup,lmp)) else res, lmp), 'rb').read()
    # extract via entries
    cnt = struct.unpack_from('<I', b, 0)[0]
    for i in range(cnt):
        p = 4+i*64
        nm = b[p:p+56].split(b'\0',1)[0].decode('latin1')
        if nm not in fns: continue
        off, size = struct.unpack_from('<II', b, p+56)
        data = b[off:off+size]
        fntpath = os.path.join(ANA, 'tmp_'+nm)
        open(fntpath, 'wb').write(data)
        f = load_font(fntpath)
        ws, hs = stats(f)
        print(f'{nm}: cnt={f["cnt"]} hgt={f["hgt"]} atlas={f["atw"]}x{f["ath"]} glyph w max={max(ws)} avg={sum(ws)/len(ws):.1f} h max={max(hs)} avg={sum(hs)/len(hs):.1f}')
        os.remove(fntpath)