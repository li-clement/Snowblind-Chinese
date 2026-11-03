#!/usr/bin/env python3
"""抓 xemu 窗口 → 裁出 640x480 游戏画面（不依赖焦点/F12）"""
import os, subprocess, sys
from PIL import Image

WL = '/Users/lee/code/iso/tools/fontcap/winlist'


def grab(out):
    tmp = '/tmp/_winraw.png'
    ids = subprocess.run([WL], capture_output=True, text=True).stdout.strip().splitlines()
    best, area = None, -1
    for ln in ids:
        p = ln.split('\t')
        if len(p) < 3:
            continue
        w, h = [int(x) for x in p[2].split('x')]
        if w * h > area:
            area, best = w * h, p[0]
    if not best:
        print('!! 找不到 xemu 窗口'); return None
    subprocess.run(['screencapture', '-l' + best, '-o', '-x', tmp], check=True)
    im = Image.open(tmp).convert('L')
    W, H = im.size
    gh = W * 3 // 4                      # 游戏区宽 = 窗宽，4:3
    top = H - gh                         # 标题条在上方
    im = im.crop((0, top, W, H)).resize((640, 480), Image.LANCZOS)
    im.save(out)
    return out
