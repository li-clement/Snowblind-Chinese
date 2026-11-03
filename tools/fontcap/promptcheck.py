#!/usr/bin/env python3
"""启动 → 轮询到主菜单 → 用规范帧判「底部 Ⓐ 确认提示在不在」。

用法: python3 promptcheck.py 名字=iso名 [...]
判据: 规范帧(严格 4:3 归一到 640x480, dy 恒 0)里 Ⓐ 圆环区峰值亮度 > 75。
      实测：提示存在 87/88/89/95，缺失 29/50 —— 峰值亮度抗呼吸闪烁，像素计数不抗。
"""
import os, re, subprocess, sys, time

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from canongrab import grab_canonical
from menu_shot import BARS, PROMPT, TOML, XEMU, ISO_DIR, ascii_prompt, ink


def is_menu(a):
    return ink(a) < 60000 and ink(a, BARS) > 500


def run_one(iso, out, budget=170, interval=2.0):
    """轮询整段启动过程，取「最像主菜单的那些帧里 Ⓐ 区的最大峰值」。

    两个必须的设计：
      1) 游戏有时会直接跳过主菜单进酒馆（实测两次），菜单判据也可能被地面长凳误触发，
         所以不"撞到菜单就收工"，而是**采满整个窗口期**再挑最好的帧；
      2) 提示会呼吸/闪烁，单帧像素计数能读出 42~885 —— 只有「多帧取峰值」抗得住。
    """
    subprocess.run(['pkill', '-9', '-f', 'MacOS/xemu'], capture_output=True)
    time.sleep(2)
    s = open(TOML).read()
    assert re.search(r'^dvd_path = ', s, re.M), 'xemu.toml 里没有 dvd_path'
    open(TOML, 'w').write(re.sub(r'^dvd_path = .*', f"dvd_path = \'{ISO_DIR}/{iso}\'", s, count=1, flags=re.M))
    with open('/tmp/xemu_run.log', 'w') as lg:
        subprocess.Popen([XEMU], stdout=lg, stderr=subprocess.STDOUT)
    time.sleep(30)
    t0 = time.time()
    n_menu = n_ok = 0
    best = (-1, None, None)        # (菜单帧里的 Ⓐ 峰值, 帧, 该帧 ink)
    any_frame = None
    while time.time() - t0 < budget:
        p = grab_canonical('/tmp/_pc.png')
        if p:
            a = np.asarray(Image.open(p), dtype=np.uint8).astype(int)
            if any_frame is None:
                any_frame = a.copy()
            if is_menu(a):
                n_menu += 1
                pr = int(a[PROMPT[0]:PROMPT[1], PROMPT[2]:PROMPT[3]].max())
                if pr > best[0]:
                    best = (pr, a.copy(), ink(a))
        n_ok += 1
        time.sleep(interval)
    subprocess.run(['pkill', '-9', '-f', 'MacOS/xemu'], capture_output=True)
    time.sleep(1)
    src = best[1] if best[1] is not None else any_frame
    if src is None:
        return f'{iso:26s} 全程抓不到有效帧 ⚠️'
    Image.fromarray(src.astype(np.uint8)).save(out)
    if best[1] is None:
        return (f'{os.path.basename(iso):26s} 采 {n_ok} 帧，没有一帧像主菜单 '
                f'（ink={ink(src)}）→ 可能直接进游戏了 ⚠️')
    return (f'{os.path.basename(iso):26s} 采 {n_ok} 帧/菜单帧 {n_menu} 帧 '
            f'全屏ink={best[2]:6d} 菜单条ink={ink(src, BARS):5d} '
            f'Ⓐ峰值(多帧最大)={best[0]:3d} → ' + ('存在 ✅' if best[0] > 75 else '缺失 ❌'))


if __name__ == '__main__':
    for spec in sys.argv[1:]:
        nm, iso = spec.split('=', 1)
        print(run_one(iso, f'analysis/{nm}.png'))
