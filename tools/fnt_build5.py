#!/usr/bin/env python3
# fnt_build5.py - CJK font rebuild with CORRECT record semantics from engine RE
# Engine (0x67580 renderer): record = 8 x u16:
#   +0 code, +2 f1, +4 f2, +6 f3, +8 f4, +A f5, +C f6, +E kerning
#   atlas rect (HALF-PIXELS): x0=f1, x1=f2, y0=f3, y1=f4  -> px = v/2
#   screen: xL=cursor-0x140; xR=xL+(f2-f1); yT=lineY-0xE0+f5; yB=yT+(f4-f3)
#   so W=f2-f1, H=f4-f3 (half-px); f5=baseline offset (half-px); f6=advance (half-px)
#   render: code & 0x7FF = record index; UTF-16 lookup by charcode.
# Record count limit 2047. Atlas UV scaled by (atw, ath) read at fontptr+0x10.
import struct, os, sys, argparse
from PIL import Image, ImageDraw, ImageFont

REC_START = 0x214

def load_font(path):
    b = open(path, 'rb').read()
    cnt, hgt = struct.unpack_from('<HH', b, 0)
    nsect, magic, offSec, offBmp = struct.unpack_from('<IIII', b, 4)
    atw, ath = struct.unpack_from('<HH', b, offBmp)
    recStart = offSec - cnt * 16
    assert recStart == REC_START, f"recStart=0x{recStart:X}"
    recs = []
    for i in range(cnt):
        recs.append(struct.unpack_from('<8H', b, recStart + i * 16))
    pre = b[0x14:REC_START]
    kerning = b[offSec:offBmp]
    meta = b[offBmp + 4: offBmp + 4 + 1076]
    return dict(b=b, cnt=cnt, hgt=hgt, nsect=nsect, magic=magic, atw=atw, ath=ath,
                start=offBmp + 1080, recs=recs, pre=pre, kerning=kerning, meta=meta)

def extract_glyph(f, v):
    """cut original glyph from atlas using f1..f4 (ABSOLUTE PIXEL rect). Returns rows or None."""
    x0, x1 = v[1], v[2]
    y0, y1 = v[3], v[4]
    atw, ath, start = f['atw'], f['ath'], f['start']
    x0 = max(0, x0); y0 = max(0, y0)
    x1 = min(x1 + 1, atw); y1 = min(y1 + 1, ath)
    w = x1 - x0; h = y1 - y0
    if w <= 0 or h <= 0:
        return None
    px = [[1 if f['b'][start + yy * atw + xx] > 127 else 0 for xx in range(x0, x1)]
          for yy in range(y0, y1)]
    if not any(any(r) for r in px):
        return None
    ys = [i for i, r in enumerate(px) if any(r)]
    xs = [j for i in range(ys[0], ys[-1] + 1) for j, vv in enumerate(px[i]) if vv]
    ox0, ox1, oy0, oy1 = min(xs), max(xs), ys[0], ys[-1]
    ox0 = max(0, ox0 - 1); ox1 = min(w - 1, ox1 + 1)
    oy0 = max(0, oy0 - 1); oy1 = min(h - 1, oy1 + 1)
    return [row[ox0:ox1 + 1] for row in px[oy0:oy1 + 1]]

def render_cjk(ch, px_h, ttf):
    big = px_h * 8
    try:
        fnt = ImageFont.truetype(ttf, big)
    except Exception:
        return None
    img = Image.new('L', (big * 2, big * 2), 0)
    d = ImageDraw.Draw(img)
    d.text((big // 2, big // 2), ch, font=fnt, fill=255)
    bbox = img.getbbox()
    if not bbox:
        return None
    img = img.crop(bbox)
    w, h = img.size
    ratio = h / big
    target_h = max(px_h * ratio, px_h * 35 // 100)
    if target_h > px_h:
        target_h = px_h
    sc = target_h / h
    nw = max(1, int(round(w * sc)))
    if nw > px_h * 2:
        nw = px_h * 2
    img = img.resize((nw, px_h), Image.LANCZOS)
    px = img.load()
    return [[1 if px[x, y] > 100 else 0 for x in range(nw)] for y in range(px_h)]

def pack_atlas(glyphs, atw):
    """glyphs: list of (code, rows, orig). pack rows into atlas; return (placed, atw, ath, atlas)"""
    x, y, row_h = 0, 0, 0
    placed = []
    rows_map = {}
    for code, rows, orig in glyphs:
        if rows is None:
            rows = []
        h = len(rows)
        w = max(len(r) for r in rows) if rows else 0
        if w <= 0 or h <= 0:
            placed.append((code, None, orig))
            continue
        if x + w + 1 > atw:
            x = 0
            y += row_h + 1
            row_h = 0
        placed.append((code, (x, y, w, h), orig))
        rows_map[code] = rows
        x += w + 1
        row_h = max(row_h, h)
    ath = y + row_h + 1
    atlas = bytearray(atw * ath)
    for code, box, orig in placed:
        if box is None:
            continue
        bx, by, w, h = box
        rows = rows_map[code]
        for yy in range(h):
            r = rows[yy]
            for xx, vv in enumerate(r):
                if vv:
                    atlas[(by + yy) * atw + bx + xx] = 255
    return placed, atw, ath, bytes(atlas)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('src'); ap.add_argument('dst'); ap.add_argument('px_h', type=int)
    ap.add_argument('--atw', type=int, default=1024)
    ap.add_argument('--ttf', default=r'C:\Windows\Fonts\msyh.ttc')
    a = ap.parse_args()
    f = load_font(a.src)

    # charset: all unique chars in translations
    cs_file = os.path.join(os.path.dirname(os.path.dirname(a.dst)), 'translation', 'jobs', 'zh_charset.txt')
    charset = open(cs_file, encoding='utf-8').read() if os.path.exists(cs_file) else ''
    have = set(v[0] for v in f['recs'] if v[0] not in (0, 0xFFFF))
    need = sorted({ord(ch) for ch in charset if ord(ch) not in have and ch not in '\n\r\t'})

    # 1) extract original glyphs (code, rows, (orig rec for f5/f6/kerning))
    entries = []
    fallback = []
    for v in f['recs']:
        c = v[0]
        if c in (0, 0xFFFF):
            continue
        if c == 32:  # space: keep as zero-rect with advance only
            entries.append((32, None, v))
            continue
        g = extract_glyph(f, v)
        if g is None:
            fallback.append(c)
            continue
        entries.append((c, g, v))
    print(f"extracted {len(entries)}/{f['cnt']} original; fallback {len(fallback)}: {''.join(chr(x) if 32 <= x < 127 else f'U+{x:X}' for x in fallback)}")

    # 2) render missing originals + all zh chars
    for c in fallback:
        g = render_cjk(chr(c), a.px_h, a.ttf)
        if g:
            entries.append((c, g, None))
    for o in need:
        g = render_cjk(chr(o), a.px_h, a.ttf)
        if g:
            entries.append((o, g, None))
    print(f"total {len(entries)} glyphs")

    # 3) pack
    placed, atw, ath, atlas = pack_atlas([(c, rows, o) for c, rows, o in entries], a.atw)

    # 4) records: code, x0*2, x1*2, y0*2, y1*2, f5, f6, kerning
    recs = bytearray()
    posmap = {(c,): box for c, box, _ in placed}
    for c, box, orig in placed:
        if c == 32 and box is None:
            recs += struct.pack('<8H', c, 0, 0, 0, 0, 0, 8, 0xFFFF)
            continue
        if box is None:
            # no bitmap: zero rect, keep advance from original if any
            adv = orig[6] if orig else 8
            f5 = orig[5] if orig else 0
            recs += struct.pack('<8H', c, 0, 0, 0, 0, f5, adv, 0xFFFF)
            continue
        bx, by, w, h = box
        if c in have and orig is not None and orig[0] != 32:
            # original latin glyph: keep baseline & advance
            f5 = orig[5]
            adv = orig[6] if orig[6] else (w + 1) * 2
            kern = orig[7]
        else:
            # new glyph (zh or fallback): baseline aligns top w/ caps (f5=6), advance = w+2 px
            f5 = 6
            adv = w + 2
            kern = 0xFFFF
        recs += struct.pack('<8H', c, bx, bx + w, by, by + h, f5, adv, kern)
    cnt = len(placed)

    offSec = REC_START + cnt * 16
    offBmp = offSec + len(f['kerning'])
    header = struct.pack('<HHIIII', cnt, a.px_h, f['nsect'], f['magic'], offSec, offBmp)
    out = header + f['pre'] + bytes(recs) + f['kerning']
    out += struct.pack('<HH', atw, ath) + f['meta'] + atlas
    open(a.dst, 'wb').write(out)
    print(f"wrote {a.dst}: {len(out)}B (cnt={cnt} hgt={a.px_h} atlas={atw}x{ath})")

if __name__ == '__main__':
    main()