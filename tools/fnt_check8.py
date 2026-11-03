import struct, os, sys
from PIL import Image

RDIR = r"E:\Game\ps5\iso\analysis"

def load_font(path):
    b = open(path, 'rb').read()
    cnt, hgt = struct.unpack_from('<HH', b, 0)
    nsect, magic, offSec, offBmp = struct.unpack_from('<IIII', b, 4)
    atw, ath = struct.unpack_from('<HH', b, offBmp)
    recStart = offSec - cnt * 16
    recs = [struct.unpack_from('<8H', b, recStart + i * 16) for i in range(cnt)]
    return dict(b=b, cnt=cnt, hgt=hgt, atw=atw, ath=ath, recs=recs, start=offBmp + 1080)

def atlas_img(f):
    atw, ath = f['atw'], f['ath']
    im = Image.new('L', (atw, ath), 0)
    px = im.load()
    for y in range(ath):
        for x in range(atw):
            v = f['b'][f['start'] + y*atw + x]
            px[x, y] = v
    return im

def show_glyphs(fname, codes):
    f = load_font(os.path.join(RDIR, fname))
    im = atlas_img(f)
    # build char->record
    bycode = {r[0]: r for r in f['recs']}
    print(f'{fname}: cnt={f["cnt"]} atlas={f["atw"]}x{f["ath"]} hgt={f["hgt"]}')
    for c in codes:
        oc = ord(c)
        if oc not in bycode:
            print(f'  {c!r} (U+{oc:04X}): NOT FOUND')
            continue
        r = bycode[oc]
        x0, x1, y0, y1 = r[1], r[2], r[3], r[4]
        blk = im.crop((x0, y0, x1, y1))
        w = blk.size[0]
        # compact print
        s = []
        for y in range(blk.size[1]):
            row = ''.join('#' if blk.getpixel((x, y)) > 100 else '.' for x in range(w))
            s.append(row)
        print(f'  {c!r}: rect=({x0},{y0})-({x1},{y1}) f5={r[5]} adv={r[6]} kern={r[7]:#x}')
        for row in s:
            print(f'      {row}')

for fn in ['gamefonta_v8.fnt', 'bigfont_v8.fnt']:
    show_glyphs(fn, ['A', 'Z', '0', '9', 'a', 'z', '.'])
show_glyphs('gamefonta_v8.fnt', ['你', '中', '文', '话'])