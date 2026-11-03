import struct, os
RES = r"E:\Game\ps5\iso\[XBOX].Baldur's.Gate.Dark.Alliance.[USA]\res"

def check(lmp, names):
    b = open(os.path.join(RES, lmp), 'rb').read()
    cnt = struct.unpack_from('<I', b, 0)[0]
    print(f'== {lmp} ({len(b)}B, {cnt} entries) ==')
    for i in range(cnt):
        p = 4 + i * 64
        nm = b[p:p + 56].split(b'\0', 1)[0].decode('latin1')
        if nm in names:
            off, size = struct.unpack_from('<II', b, p + 56)
            fb = b[off:off + size]
            c, h = struct.unpack_from('<HH', fb, 0)
            ns, mag, offSec, offBmp = struct.unpack_from('<IIII', fb, 4)
            atw, ath = struct.unpack_from('<HH', fb, offBmp)
            recStart = offSec - c * 16
            print(f'  {nm}: cnt={c} hgt={h} offSec={offSec:#x} offBmp={offBmp:#x} atw={atw} ath={ath} recStart={recStart:#x} recOOB={recStart!=0x214}')

check('font.lmp', ['gamefonta.fnt', 'gamefontmed.fnt', 'gamefontsmall.fnt'])
check('frontend.lmp', ['bigfont.fnt', 'creditfont.fnt', 'gamefontsmall.fnt'])
# sorted check
for lmp in ['font.lmp', 'frontend.lmp']:
    b = open(os.path.join(RES, lmp), 'rb').read()
    cnt = struct.unpack_from('<I', b, 0)[0]
    names = [b[4 + i * 64: 4 + i * 64 + 56].split(b'\0', 1)[0].decode('latin1') for i in range(cnt)]
    print(f'{lmp} sorted: {names == sorted(names)}')