import struct
b = open(r'E:\Game\ps5\iso\analysis\gamefonta.fnt', 'rb').read()
cnt, hgt = struct.unpack_from('<HH', b, 0)
nsect, magic, offSec, offBmp = struct.unpack_from('<IIII', b, 4)
print(f'cnt={cnt} hgt={hgt} nsect={nsect} magic={magic:#x} offSec={offSec:#x} offBmp={offBmp:#x}')
print('--- atw/ath at offBmp ---')
print(f'  {bytes(b[offBmp:offBmp+16]).hex()}')
atw, ath = struct.unpack_from('<HH', b, offBmp)
print(f'  atw={atw} ath={ath}')
print('--- meta 1076 bytes at offBmp+4 ---')
for i in range(0, 1076, 16):
    chunk = b[offBmp+4+i:offBmp+4+i+16]
    u16s = struct.unpack_from('<8H', chunk)
    print(f'  +{i:4d}: ' + ' '.join(f'{u:04x}' for u in u16s))
print('--- atlas size ---')
print(f'  atlas bytes = {atw * ath}, file len = {len(b)}, tail = {offBmp+4+1076+atw*ath}')