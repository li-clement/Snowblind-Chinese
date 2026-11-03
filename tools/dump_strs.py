import struct
b = open(r"E:\Game\ps5\iso\[XBOX].Baldur's.Gate.Dark.Alliance.[USA]\default.xbe", 'rb').read()
# .rdata VA = file_off + 0x115A0 (per earlier verified relation)
def rd(va, n=64):
    off = va - 0x115A0
    return b[off:off+n]

for va, label in [(0x138958, 'lmp name?'), (0x13F228, 'font name?'), (0x13E924, 'path fmt?'), (0x13E91C, 'path fmt2?'), (0x13E8B4, 'ext .fnt?'), (0x13E8C0, 'ext?'), (0x13EDB8, 'ext?'), (0x141AB4, 'ext?'), (0x141AB0, 'ext?'), (0x141AA8, 'ext?'), (0x141A98, 'ext?'), (0x141AAC, 'ext?'), (0x13D8B5, 'gamefont?')]:
    raw = rd(va)
    # printable chars until null
    s = raw.split(b'\x00')[0]
    try:
        txt = s.decode('latin1')
    except Exception:
        txt = repr(s)
    print(f'{label} @0x{va:X}: {txt!r}')