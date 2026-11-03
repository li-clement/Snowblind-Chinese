#!/usr/bin/env python3
# fnt_build2.py - fully rebuild a .fnt with system-font glyphs (ASCII + zh charset)
#   usage: fnt_build2.py <out.fnt> <px_h> <coord_mode:px|half> <ttf>
#   layout mirrors original: header(20) + 0x14..0x100 zero + 0x100..0x214 zero
#                            + records(16*cnt) + kerning(24B empty) + (atw,ath,u16 u32 0x44C0,0x38)
#                            + 1080B meta(zeros) + atlas 8bpp
import struct, os, sys
from PIL import Image, ImageDraw, ImageFont

def render_glyph(ch, px_h, ttf, w_cell=None):
    """Render one glyph to 0/1 rows. Returns list of px_h rows.
    Big canvas, centered, then ink-bbox crop, then scale so the glyph's em-ratio
    is preserved, but tiny glyphs (punctuation) get a minimum display size."""
    big = px_h * 8
    fnt = ImageFont.truetype(ttf, big)
    img = Image.new('L', (big * 2, big * 2), 0)
    d = ImageDraw.Draw(img)
    d.text((big // 2, big // 2), ch, font=fnt, fill=255)
    bbox = img.getbbox()
    if not bbox:
        return None
    img = img.crop(bbox)
    w, h = img.size
    # target height: preserve em ratio, but enforce a readable minimum
    ratio = h / big
    target_h = max(px_h * ratio, px_h * 35 // 100)
    if target_h > px_h:
        target_h = px_h
    sc = target_h / h
    nw = max(1, int(round(w * sc)))
    if nw > px_h * 2:            # cap: allow wide dashes/ellipsis, nothing absurd
        nw = px_h * 2
    img = img.resize((nw, px_h), Image.LANCZOS)
    px = img.load()
    return [[1 if px[x, y] > 100 else 0 for x in range(nw)] for y in range(px_h)]

def pack_atlas(glyphs, atw=512):
    """glyphs: list of (code, rows). returns (atw, ath, pos[(code,rows,x,y)], atlas_bytes)"""
    x, y, row_h = 0, 0, 0
    pos = []
    for code, rows in glyphs:
        h = len(rows)
        w = max(len(r) for r in rows)
        if x + w + 1 > atw:
            x = 0
            y += row_h + 1
            row_h = 0
        pos.append((code, rows, x, y))
        x += w + 1
        row_h = max(row_h, h)
    ath = y + row_h + 1
    atlas = bytearray(atw * ath)
    for code, rows, bx, by in pos:
        for yy, row in enumerate(rows):
            for xx, v in enumerate(row):
                if v:
                    atlas[(by + yy) * atw + bx + xx] = 255
    return atw, ath, pos, bytes(atlas)

def main():
    dst = sys.argv[1]
    px_h = int(sys.argv[2])
    mode = sys.argv[3]               # 'px' or 'half'
    ttf = sys.argv[4] if len(sys.argv) > 4 else r'C:\Windows\Fonts\msyh.ttc'
    charset_file = os.path.join(os.path.dirname(dst), '..', 'translation', 'jobs', 'zh_charset.txt')
    charset = open(charset_file, encoding='utf-8').read() if os.path.exists(charset_file) else ''

    codes = []
    for o in range(0x20, 0x7F):      # ASCII printable
        codes.append(o)
    seen = set(codes)
    for ch in charset:
        o = ord(ch)
        if o not in seen and ch not in '\n\r\t':
            codes.append(o)
            seen.add(o)
    codes.sort()

    glyphs = []
    miss = 0
    for o in codes:
        ch = chr(o)
        if o == 0x20:  # space -> blank cell
            glyphs.append((o, [[0] * (px_h // 2) for _ in range(px_h)]))
            continue
        g = render_glyph(ch, px_h, ttf)
        if g is None:
            glyphs.append((o, [[0] * (px_h // 2) for _ in range(px_h)]))
            miss += 1
            continue
        glyphs.append((o, g))
    atw, ath, pos, atlas = pack_atlas(glyphs)
    cnt = len(glyphs)

    recs = bytearray()
    for code, rows, x, y in pos:
        w_px = max(len(r) for r in rows) if rows else 2
        mult = 2 if mode == 'half' else 1
        recs += struct.pack('<8H', code, y * mult, x * mult, 0, px_h * mult,
                            px_h // 2, w_px * mult, 0xFFFF)

    offSec = 0x214 + cnt * 16
    kerning = struct.pack('<6H', 0x0100, 0x0100, 0, 0xFFFF, 0xFFFF, 0)  # empty kerning, 12B -> pad
    kerning = bytes(24)              # jap-style empty region
    offBmp = offSec + len(kerning)
    header = struct.pack('<HHIIII', cnt, px_h, 2, 0x214, offSec, offBmp)
    pre = bytes(0x100 - 20)          # 0x14..0xFF
    meta_region = bytes(14)          # atw u16 + ath u16 + 4x16 bytes (like original 0x44C0,0x38 magic)
    out = header + pre + bytes(0x214 - 0x100) + bytes(recs) + kerning
    out += struct.pack('<HH', atw, ath) + bytes(1076) + atlas
    open(dst, 'wb').write(out)
    print(f"{dst}: cnt={cnt} px_h={px_h} mode={mode} atlas={atw}x{ath} offSec=0x{offSec:X} offBmp=0x{offBmp:X} bytes={len(out)}")

if __name__ == '__main__':
    main()