import struct, os
ANA = r'E:\Game\ps5\iso\analysis'
def show(path, label):
    b = open(path, 'rb').read()
    cnt, hgt = struct.unpack_from('<HH', b, 0)
    nsect, magic, offSec, offBmp = struct.unpack_from('<IIII', b, 4)
    v34 = struct.unpack_from('<I', b, 0x34)[0]
    v38 = struct.unpack_from('<I', b, 0x38)[0]
    print(f'{label}: len={len(b)} cnt={cnt} hgt={hgt} magic={magic:#x} offSec={offSec:#x} offBmp={offBmp:#x}')
    print(f'  +0x34={v34:#x}  +0x38={v38:#x}')
    # dump 0x14..0x214 pre first 64 bytes
    print(f'  pre[0x14:0x54] = {b[0x14:0x54].hex()}')
    if v34 and v34 < len(b):
        print(f'  table@ +0x34 -> file off {v34:#x}: {b[v34:v34+64].hex()}')
    if v38 and v38 < len(b):
        print(f'  table@ +0x38 -> file off {v38:#x}: {b[v38:v38+64].hex()}')

show(os.path.join(ANA, 'gamefonta.fnt'), 'ORIG gamefonta')
show(os.path.join(ANA, 'gamefonta_v8.fnt'), 'V8   gamefonta')
show(os.path.join(ANA, 'bigfont.fnt'), 'ORIG bigfont')
show(os.path.join(ANA, 'bigfont_v8.fnt'), 'V8   bigfont')
show(os.path.join(ANA, 'japfontbig0.fnt') if os.path.exists(os.path.join(ANA,'japfontbig0.fnt')) else r"E:\Game\ps5\iso\[XBOX].Baldur's.Gate.Dark.Alliance.[USA]\res\frontend.lmp", 'japfontbig0?')