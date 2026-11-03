import struct, os
ana = r'E:\Game\ps5\iso\analysis'
names = ['gamefonta.fnt','gamefontmed.fnt','gamefontsmall.fnt','bigfont.fnt','creditfont.fnt','japfontbig0.fnt','japfontsmall0.fnt']
for fn in names:
    p = os.path.join(ana, fn)
    if not os.path.exists(p):
        # try backup_original
        p2 = os.path.join(r'E:\Game\ps5\iso\backup_original', fn)
        if os.path.exists(p2): p = p2
        else:
            print(f'{fn}: MISSING'); continue
    b = open(p,'rb').read()
    cnt, hgt = struct.unpack_from('<HH', b, 0)
    nsect, magic, offSec, offBmp = struct.unpack_from('<IIII', b, 4)
    print(f'{fn}: len={len(b)} cnt={cnt} hgt={hgt} nsect={nsect} magic={magic:#x} offSec={offSec:#x} offBmp={offBmp:#x}')
    if offBmp < len(b):
        atw, ath = struct.unpack_from('<HH', b, offBmp)
        print(f'   atlas={atw}x{ath}')
    else:
        print(f'   offBmp OUT OF RANGE')
    # check v5 exist
    v5 = os.path.join(ana, fn.replace('.fnt','_v5.fnt'))
    if os.path.exists(v5):
        b2 = open(v5,'rb').read()
        c2, h2 = struct.unpack_from('<HH', b2, 0)
        n2, m2, o2, o3 = struct.unpack_from('<IIII', b2, 4)
        atw2, ath2 = struct.unpack_from('<HH', b2, o3)
        print(f'   v5: len={len(b2)} cnt={c2} hgt={h2} nsect={n2} magic={m2:#x} offSec={o2:#x} offBmp={o3:#x} atlas={atw2}x{ath2}')