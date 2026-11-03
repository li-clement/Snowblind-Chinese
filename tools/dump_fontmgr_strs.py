import struct
b = open(r"E:\Game\ps5\iso\[XBOX].Baldur's.Gate.Dark.Alliance.[USA]\default.xbe", 'rb').read()
# .rdata VA = file_off + 0x115A0
def rd(va, n=96):
    off = va - 0x115A0
    return b[off:off + n]

# font manager string cluster around 0x13ED24
for va in [0x13ED24, 0x13ED34, 0x13ED40, 0x13ED4C, 0x13ED58, 0x13ED64,
           0x13ED78, 0x13ED88, 0x13ED98, 0x13EDA4, 0x13EDB0, 0x13EBC0,
           0x13EB90, 0x13EBA8, 0x13EC90, 0x13EDD0, 0x13EDE0, 0x13EDF8]:
    raw = rd(va, 64)
    s = raw.split(b'\x00')[0]
    try:
        txt = s.decode('latin1')
    except Exception:
        txt = repr(s)
    if txt:
        print(f'0x{va:X}: {txt!r}')