import struct
RES = r"E:\Game\ps5\iso\[XBOX].Baldur's.Gate.Dark.Alliance.[USA]\res"

def verify(path):
    b = open(path, 'rb').read()
    c = struct.unpack_from('<I', b, 0)[0]
    print(f'== {path.split(chr(92))[-1]}: {len(b)}B {c} entries ==')
    ok = True
    cur = 4 + c * 64
    cur = (cur + 0x7F) & ~0x7F
    for i in range(c):
        p = 4 + i * 64
        nm = b[p:p + 56].split(b'\x00', 1)[0].decode('latin1')
        off, sz = struct.unpack_from('<II', b, p + 56)
        rec_ok = off == cur and off % 0x80 == 0 and off + sz <= len(b)
        if not rec_ok:
            ok = False
        print(f'  #{i:2d} {nm:<24s} off=0x{off:X} sz={sz} expected=0x{cur:X} {"OK" if rec_ok else "<<< BAD"}')
        cur = (off + sz + 0x7F) & ~0x7F
    print(f'  -> recursive 0x80 layout valid: {ok}')

verify(RES + r'\font.lmp')
verify(RES + r'\frontend.lmp')