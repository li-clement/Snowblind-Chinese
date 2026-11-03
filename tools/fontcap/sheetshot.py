#!/usr/bin/env python3
"""底部拼图取证：不依赖任何裁剪几何假设，直接把原始窗口图的底部若干帧拼一张图给人眼判。

为什么不用数值判据（Ⓐ 区峰值）：规范裁剪在**暗场景**下会失效——主菜单背景极暗时
「非黑行段」塌到中间亮带，画面宽被算小、底部提示区直接被裁掉（v22 就量出了无效的 54）。
原始窗口图永远包含完整画面，取底部一条拼起来，一眼就能看出「Ⓐ 确认」在不在。

用法: python3 sheetshot.py 名字=iso名 [采样秒数表]
输出: analysis/sheet_<名字>.png（8 条底部带，每条前标采样时刻）+ 同名 _full.png（末帧全景）
"""
import os, re, subprocess, sys, time

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from canongrab import window_id

XEMU = '/Users/lee/game/xemu-0.8.139-macos-universal/xemu.app/Contents/MacOS/xemu'
TOML = os.path.expanduser('~/Library/Application Support/Xemu/xemu/xemu.toml')
ISO_DIR = '/Users/lee/code/iso'
AN = os.path.join(ISO_DIR, 'analysis')


def raw(path):
    wid = window_id()
    if not wid:
        return None
    subprocess.run(['screencapture', '-l', wid, '-o', '-x', path], capture_output=True)
    return path if os.path.exists(path) else None


def run(iso, name, times=(45, 62, 79, 96, 113, 130, 147, 164)):
    subprocess.run(['pkill', '-9', '-f', 'MacOS/xemu'], capture_output=True)
    time.sleep(2)
    s = open(TOML).read()
    assert re.search(r'^dvd_path = ', s, re.M), 'xemu.toml 里没有 dvd_path'
    open(TOML, 'w').write(re.sub(r'^dvd_path = .*', f"dvd_path = '{ISO_DIR}/{iso}'", s, count=1, flags=re.M))
    with open('/tmp/xemu_run.log', 'w') as lg:
        subprocess.Popen([XEMU], stdout=lg, stderr=subprocess.STDOUT)
    strips = []
    last = None
    for t in times:
        wait = t - (times[0] if t == times[0] else 0)
        if t == times[0]:
            time.sleep(t)
        p = raw('/tmp/_raw.png')
        if p:
            im = Image.open(p).convert('L')
            W, H = im.size
            last = im.copy()
            band = im.crop((0, int(H * 0.66), W, H))          # 底部 34%：提示行一定在里面
            band = band.resize((760, int(band.size[1] * 760 / W)), Image.LANCZOS)
            strips.append((f't={t}s  {W}x{H}', band))
        if t != times[-1]:
            time.sleep(times[times.index(t) + 1] - t)
    subprocess.run(['pkill', '-9', '-f', 'MacOS/xemu'], capture_output=True)
    if not strips:
        print(f'{name}: 抓不到帧')
        return None
    th = sum(b.size[1] + 16 for _, b in strips)
    out = Image.new('L', (760, th), 20)
    d = ImageDraw.Draw(out)
    y = 0
    for lab, b in strips:
        d.text((4, y + 2), lab, fill=255)
        out.paste(b, (0, y + 14))
        y += b.size[1] + 16
    op = os.path.join(AN, f'sheet_{name}.png')
    out.save(op)
    if last is not None:
        last.resize((760, int(last.size[1] * 760 / last.size[0]))).save(os.path.join(AN, f'sheet_{name}_full.png'))
    print(f'{name}: {op}（{len(strips)} 帧） + _full.png')
    return op


if __name__ == '__main__':
    for spec in sys.argv[1:]:
        nm, iso = spec.split('=', 1)
        run(iso, nm)
