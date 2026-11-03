import struct
RES = r"E:\Game\ps5\iso\[XBOX].Baldur's.Gate.Dark.Alliance.[USA]\res"
for lmp in ('font.lmp', 'frontend.lmp'):
    b = open(RES + '\\' + lmp, 'rb').read()
    c = struct.unpack_from('<I', b, 0)[0]
    print(lmp, len(b), 'entries', c)