#!/usr/bin/env python3
"""离线排版预览：直接从构建出来的 .lmp 里取图集像素 + 记录表，按引擎的前进量规则排一行字。

为什么要它：标点和行宽的调优，靠开机回一轮要 3 分钟还占用模拟器；这里 1 秒出图，
排出来的位置和真机一致（同样的 rect + 同样的 f6 步进）。

用法: python3 preview_line.py "要排的字" [字体名] [放大倍数]
"""
import struct, sys, os
from PIL import Image

TREE = "/Users/lee/code/iso/[XBOX].Baldur's.Gate.Dark.Alliance.[USA]/res"
SCALE = 3


def load_font(lmp, want):
    b = open(os.path.join(TREE, lmp), 'rb').read()
    for i in range(struct.unpack_from('<I', b, 0)[0]):
        q = 4 + i * 64
        nm = b[q:q + 56].split(b'\0')[0].decode('latin1')
        if nm != want:
            continue
        off = struct.unpack_from('<I', b, q + 56)[0]
        cnt, _, _, recs, _, offBmp = struct.unpack_from('<HHIIII', b, off)
        if recs + cnt * 16 > len(b) - off:
            return None                      # 薄头：跟 master 一样的图集，换个名字再看一次
        atw, ath = struct.unpack_from('<HH', b, off + offBmp)
        pix = off + offBmp + 0x438
        atlas = Image.frombytes('L', (atw, ath), b[pix:pix + atw * ath])
        cmap = struct.unpack_from('<256H', b, off + 0x14)
        R = {}
        for j in range(cnt):
            c, x0, x1, y0, y1, f5, f6, k = struct.unpack_from('<8H', b, recs + j * 16)
            if c == 0xFFFF:
                continue
            R[c] = (x0, x1, y0, y1, f6)
        return atlas, R, cmap, (atw, ath)
    return None


def render(text, want='gamefonta.fnt', scale=SCALE):
    f = load_font('font.lmp', want) or load_font('frontend.lmp', want)
    if not f:
        sys.exit(f'容器里找不到完整的 {want}（可能是薄头，换 master 名字）')
    atlas, R, cmap, (atw, ath) = f
    adv = {}
    for c, (x0, x1, y0, y1, a) in R.items():
        adv[c] = a
    hs = [y1 - y0 + 1 for (x0, x1, y0, y1, a) in R.values() if y1 >= y0]
    top = max(y1 - y0 + 1 for (x0, x1, y0, y1, a) in R.values()) if hs else 20
    W = sum(adv.get(ord(ch), 8) for ch in text) + 8
    img = Image.new('L', (W, top + 6), 0)
    pen = 4
    for ch in text:
        c = ord(ch)
        cell = cmap[c] if c < 256 else None          # 8 位路径只走 charmap
        r = R.get(c)
        if r is None:
            pen += 8
            continue
        x0, x1, y0, y1, a = r
        w, h = x1 - x0 + 1, y1 - y0 + 1
        if w > 0 and h > 0:
            g = atlas.crop((x0, y0, x1 + 1, y1 + 1))
            img.paste(g, (pen, 3 + (top - h) - (top - h) // 2 - (top - h) // 2 if False else max(0, (top - h) // 2)))
        pen += a
    return img.resize((img.size[0] * scale, img.size[1] * scale), Image.NEAREST), pen - 8, want


if __name__ == '__main__':
    text = sys.argv[1] if len(sys.argv) > 1 else '我希望能请你帮个忙，我在街上被一伙盗贼抢了，我想找到他们。'
    want = sys.argv[2] if len(sys.argv) > 2 else 'gamefonta.fnt'
    sc = int(sys.argv[3]) if len(sys.argv) > 3 else SCALE
    img, w, want = render(text, want, sc)
    out = f'/Users/lee/code/iso/analysis/preview_{want.split(".")[0]}.png'
    img.save(out)
    print(f'{want}: "{text}" {len(text)} 字 → 总宽 {w}px（640 宽屏占 {w/640*100:.0f}%）  {out}')
