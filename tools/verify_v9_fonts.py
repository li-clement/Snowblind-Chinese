import struct
RES = r"E:\Game\ps5\iso\[XBOX].Baldur's.Gate.Dark.Alliance.[USA]\res"

def chk(lmp):
    b = open(RES + '\\' + lmp, 'rb').read()
    c = struct.unpack_from('<I', b, 0)[0]
    print(f'== {lmp} ==')
    names = []
    for i in range(c):
        p = 4 + i * 64
        nm = b[p:p + 56].split(b'\x00', 1)[0].decode('latin1')
        names.append(nm)
        off, sz = struct.unpack_from('<II', b, p + 56)
        fb = b[off:off + sz]
        cnt, hgt = struct.unpack_from('<HH', fb, 0)
        nsect, magic, oSec, oBmp = struct.unpack_from('<IIII', fb, 4)
        atw = ath = 0
        rec_start = 0x214
        if oBmp + 2 <= sz:
            atw, ath = struct.unpack_from('<HH', fb, oBmp)
        rec_end = oSec or (cnt * 16 + rec_start)
        print(f'  {nm:<20s} sz={sz} cnt={cnt} hgt={hgt} magic={magic:#x} offSec={oSec:#x} offBmp={oBmp:#x} atw={atw} ath={ath} srt={names == sorted(names)}')

chk('font.lmp')
chk('frontend.lmp')