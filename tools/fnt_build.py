#!/usr/bin/env python3
# fnt_build.py - rebuild a .fnt: keep structure, repack atlas with original latin glyphs + zh CJK glyphs
#   layout: 0x00 header(20B) | 0x100..0x213 legacy region (copied) | records @0x214 (16B each)
#           | kerning region (copied) | offBmp: u16 atw,u16 ath + 1080B metadata (copied)
#           | atlas 8bpp at offBmp+1080
# usage: fnt_build.py <in.fnt> <out.fnt> <glyph_px_h> [font_ttf]
import struct, os, sys
from PIL import Image, ImageDraw, ImageFont

LEGACY = 0x100          # 0x100..0x214 (276 bytes) kept verbatim
REC_START = 0x214

def load_font(path):
    b = open(path, 'rb').read()
    cnt, hgt = struct.unpack_from('<HH', b, 0)
    nsect, magic, offSec, offBmp = struct.unpack_from('<IIII', b, 4)
    atw, ath = struct.unpack_from('<HH', b, offBmp)
    start = offBmp + 1080
    recStart = offSec - cnt * 16
    assert recStart == REC_START, f"unexpected recStart 0x{recStart:X}"
    recs = []
    for i in range(cnt):
        o = recStart + i * 16
        vals = struct.unpack_from('<8H', b, o)
        recs.append(vals)
    pre_legacy = b[0x14:LEGACY]      # bytes 0x14..0x100
    legacy = b[LEGACY:REC_START]     # bytes 0x100..0x214
    kstart = offSec
    ksize = offBmp - offSec
    kerning = b[kstart:kstart + ksize]
    meta = b[offBmp + 4: offBmp + 4 + 1080]
    return dict(b=b, cnt=cnt, hgt=hgt, nsect=nsect, magic=magic, atw=atw, ath=ath,
                start=start, recs=recs, pre_legacy=pre_legacy, legacy=legacy,
                kerning=kerning, meta=meta)

def extract_glyph(f, vals, pad=1):
    """cut original glyph bitmap (ink bbox + pad) from atlas using (vals[1]/2, vals[2]/2)
    window is generously large; exact ink bbox is then cropped"""
    b, atw, ath, start = f['b'], f['atw'], f['ath'], f['start']
    y, x = vals[1] // 2, vals[2] // 2
    win_w = min(40, atw - x)
    win_h = min(48, ath - y)
    if win_w <= 0 or win_h <= 0:
        return None
    px = []
    for yy in range(y, y + win_h):
        row = b[start + yy * atw + x: start + yy * atw + x + win_w]
        px.append([1 if v > 127 else 0 for v in row])
    if not any(any(r) for r in px):
        return None
    ys = [i for i, r in enumerate(px) if any(r)]
    y0, y1 = ys[0], ys[-1]
    xs = [j for i in range(y0, y1 + 1) for j, v in enumerate(px[i]) if v]
    x0, x1 = min(xs), max(xs)
    x0 = max(0, x0 - pad); x1 = min(win_w - 1, x1 + pad)
    y0 = max(0, y0 - pad); y1 = min(win_h - 1, y1 + pad)
    return [row[x0:x1 + 1] for row in px[y0:y1 + 1]]

def render_cjk(ch, px_h, ttf):
    """render a CJK char to 0/1 rows, tall=px_h, square-ish"""
    size = px_h * 4
    fnt = ImageFont.truetype(ttf, size)
    img = Image.new('L', (size, size), 0)
    d = ImageDraw.Draw(img)
    d.text((size // 20, size // 20), ch, font=fnt, fill=255)
    # crop ink
    bbox = img.getbbox()
    if not bbox:
        return None
    img = img.crop(bbox)
    w, h = img.size
    scale = px_h / h
    nw, nh = max(1, int(round(w * scale))), px_h
    img = img.resize((nw, nh), Image.LANCZOS)
    px = img.load()
    return [[1 if px[x, y] > 127 else 0 for x in range(nw)] for y in range(nh)]

def pack(entries):
    """shelf-pack glyphs (list of (code, rows)) into atlas. returns (atw, ath, pos map)"""
    W = 512
    x, y, row_h = 0, 0, 0
    positions = []
    for code, rows in entries:
        h = len(rows)
        w = max(len(r) for r in rows)
        if x + w > W:
            x = 0
            y += row_h
            row_h = 0
        row_h = max(row_h, h)
        positions.append((code, rows, x, y))
        x += w + 1
    ath = y + row_h
    return positions, W, ath

def main():
    src, dst = sys.argv[1], sys.argv[2]
    px_h = int(sys.argv[3]) if len(sys.argv) > 3 else 12
    ttf = sys.argv[4] if len(sys.argv) > 4 else None
    if ttf is None:
        for cand in [r'C:\Windows\Fonts\msyh.ttc', r'C:\Windows\Fonts\simhei.ttf',
                     r'C:\Windows\Fonts\Deng.ttf', r'C:\Windows\Fonts\msyhbd.ttc']:
            if os.path.exists(cand):
                ttf = cand
                break
    print(f"render font: {ttf} px_h={px_h}")
    f = load_font(src)

    # charset: original records (by char) + zh CJK not present
    charset = open(os.path.join(os.path.dirname(os.path.dirname(src)), 'translation', 'jobs', 'zh_charset.txt'),
                   encoding='utf-8').read() if os.path.exists(os.path.join(os.path.dirname(os.path.dirname(src)),
                   'translation', 'jobs', 'zh_charset.txt')) else ''
    if not charset:
        charset = '，。！？；：""''（）—…·'
    have = set()
    for vals in f['recs']:
        if vals[0] != 0xFFFF:
            have.add(vals[0])
    need = []
    for ch in charset:
        o = ord(ch)
        if o not in have and ch not in ('\n', '\r', '\t'):
            need.append(ch)
    need = sorted(set(need), key=ord)
    print(f"original {f['cnt']} records; adding {len(need)} chars from zh charset")

    entries = []  # (code, rows)
    # 1) original latin glyphs (keep style)
    for vals in f['recs']:
        c = vals[0]
        if c == 0xFFFF or c == 0:
            continue
        g = extract_glyph(f, vals)
        if g is None:
            continue
        entries.append((c, g))
    print(f"kept {len(entries)} original glyphs")
    # 2) new zh glyphs
    added = 0
    for ch in need:
        g = render_cjk(ch, px_h, ttf)
        if g is None:
            continue
        entries.append((ord(ch), g))
        added += 1
    print(f"rendered {added} zh glyphs")

    # pack
    W = 512
    positions = []
    x, y, row_h = 0, 0, 0
    for code, rows in entries:
        h = len(rows)
        w = max(len(r) for r in rows)
        if x + w > W:
            x = 0
            y += row_h
            row_h = 0
        row_h = max(row_h, h)
        positions.append((code, rows, x, y))
        x += w + 1
    ath = y + row_h
    print(f"atlas {W}x{ath}")

    # build atlas bytes 8bpp
    atlas = bytearray(W * ath)
    for code, rows, x, y in positions:
        for yy, row in enumerate(rows):
            for xx, v in enumerate(row):
                if v:
                    atlas[(y + yy) * W + x + xx] = 255
    atlas = bytes(atlas)

    # records: (char, y*2, x*2, f3, f4, f5, f6, FFFF)
    # follow original convention: use f3..f6 template from original ' ' or a typical cap
    template = None
    for vals in f['recs']:
        if vals[0] == ord('A'):
            template = vals[3:7]
            break
    if template is None:
        template = (0, 0, 0, 24)
    recs = bytearray()
    order = sorted(positions, key=lambda t: t[0])
    for code, rows, x, y in order:
        w_px = max(len(r) for r in rows)
        recs += struct.pack('<8H', code, y * 2, x * 2, template[0], template[1],
                            template[2], max(8, w_px) * 2, 0xFFFF)
    cnt = len(order)

    # assemble
    offSec = REC_START + cnt * 16
    kerning = f['kerning'] if len(f['kerning']) >= 24 else bytes(24)
    offBmp = offSec + len(kerning)
    header = struct.pack('<HHIIII', cnt, px_h, f['nsect'], f['magic'], offSec, offBmp)
    out = header + f['pre_legacy'] + f['legacy'] + bytes(recs) + kerning
    out += struct.pack('<HH', W, ath) + f['meta'] + atlas
    open(dst, 'wb').write(out)
    print(f"wrote {dst}: {len(out)} bytes (cnt={cnt}, atw={W}, ath={ath}, offSec=0x{offSec:X}, offBmp=0x{offBmp:X})")

if __name__ == '__main__':
    main()