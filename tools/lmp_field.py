import struct
b = open(r'E:\Game\ps5\iso\backup_original\font.lmp', 'rb').read()
cnt = struct.unpack_from('<I', b, 0)[0]
print(f'cnt={cnt} len={len(b)}')
for i in range(cnt):
    p = 4 + i*64
    name = b[p:p+56].split(b'\0',1)[0].decode('latin1')
    d_56 = struct.unpack_from('<I', b, p+56)[0]
    d_60 = struct.unpack_from('<I', b, p+60)[0]
    print(f'entry{i}: name={name!r}')
    print(f'  u32@+56=0x{d_56:x} ({d_56})   u32@+60=0x{d_60:x} ({d_60})')
    # try: off=@56 size=@60
    print(f'  if off@56/size@60: off={d_56} size={d_60}')
    # try: size=@56 off=@60
    print(f'  if size@56/off@60: size={d_56} off={d_60}')
    # where does the file content start? check 0x100 region
    print(f'  bytes@0xE0: {b[0xE0:0x104].hex()}')
    break
# entries 1..2
for i in range(1, cnt):
    p = 4 + i*64
    name = b[p:p+56].split(b'\0',1)[0].decode('latin1')
    d_56 = struct.unpack_from('<I', b, p+56)[0]
    d_60 = struct.unpack_from('<I', b, p+60)[0]
    print(f'entry{i}: name={name!r} u32@56={d_56} u32@60={d_60}')