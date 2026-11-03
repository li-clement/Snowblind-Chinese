#!/usr/bin/env python3
"""窗口无关的规范抓帧：把 xemu 窗口里的 4:3 画面**检测**出来再归一到 640x480。

为什么不用原来的推算裁剪（top = H - W*3/4）：那是假设「游戏区底边贴着窗口底、
且窗口高度不含标题栏」。实测 xemu 窗口尺寸一变（740x660 ↔ 1280x988），整体偏移就跳到
十几像素（dy 从 14 变 3），Ⓐ 提示的判据框跟着失效。这里改成从像素里找画面边界：

  1. 逐行找「非黑行」——macOS 标题栏是均匀的短灰带，游戏内容是一大片连续行，取底部那片；
  2. 画面底边 = 从下往上第一条非黑行；高度 = 宽 * 3/4（严格 4:3），向上取顶边；
  3. 宽度 = 在该框中部横带上找最长的非黑列段；
  4. 框内平均亮度太低（黑屏/淡入淡出）就返回 None，让调用方重试，绝不返回半张图。

于是归一化之后 dy 恒为 0，判据框可以写死。
"""
import os, subprocess, sys, tempfile

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _win_image():
    from winlist import list_windows  # 只在需要时用（编译好的小工具）
    return None


def window_id():
    """最大的那个窗口就是 xemu 游戏窗口（winlist 输出 id\\towner\\tWxH）"""
    out = subprocess.run([os.path.join(os.path.dirname(os.path.abspath(__file__)), 'winlist')],
                         capture_output=True, text=True).stdout
    best, bid = -1, None
    for ln in out.splitlines():
        f = ln.split('\t')
        if len(f) < 3:
            continue
        try:
            w, h = map(int, f[2].lower().split('x'))
        except Exception:
            continue
        if w * h > best:
            best, bid = w * h, f[0]
    return bid


def grab_canonical(out, dark_floor=10):
    """抓一帧并归一到 640x480。返回 out 路径，或 None（没检测到有效画面）"""
    wid = window_id()
    if not wid:
        return None
    with tempfile.TemporaryDirectory() as td:
        raw = os.path.join(td, 'raw.png')
        subprocess.run(['screencapture', '-l', wid, '-o', '-x', raw], capture_output=True)
        if not os.path.exists(raw):
            return None
        a = np.asarray(Image.open(raw).convert('L'), dtype=np.int16)
        H, W = a.shape
        rowink = (a > 24).sum(axis=1)
        nonblack = rowink > 0.15 * W
        if not nonblack.any():
            return None

        def longest_run(mask):
            best = run = 0; end = -1
            for k, v in enumerate(mask):
                run = run + 1 if v else 0
                if run > best:
                    best, end = run, k
            return (end - best + 1, end) if best else (0, -1)

        # 垂直：取最长的连续「非黑行段」。macOS 标题栏只是一条短灰带，会被当成另一段，
        # 不会再像以前那样用 W*3/4 从底边硬推高度 —— 窗口比 4:3 宽时那个框会顶到标题栏，
        # 于是整幅画面下移、底部 Ⓐ 提示被裁掉（对照实验里 v20 就是这么被误判成"提示缺失"的）。
        run_h, r_end = longest_run(nonblack)
        if run_h < 120:
            return None
        r_top = r_end - run_h + 1
        # 水平：在该段中部横带上找最长非黑列段 = 画面宽
        mid = a[r_top + run_h // 3: r_top + 2 * run_h // 3]
        colink = (mid > 24).mean(axis=0)
        gw, x1 = longest_run(colink > 0.15)
        if gw < 0.4 * W:
            gw, x1 = W, W - 1
        x0 = x1 - gw + 1
        # 严格 4:3：以画面宽推高度，底边对齐（Ⓐ 提示贴在画面底部，绝不能裁掉）
        gh = int(round(gw * 3 / 4))
        if gh > run_h:                       # 段高不足（画面上下还有黑边）→ 以段高为准反推宽
            gh = run_h
            gw2 = int(round(gh * 4 / 3))
            cx = (x0 + x1) // 2
            x0, x1 = max(0, cx - gw2 // 2), min(W - 1, cx - gw2 // 2 + gw2 - 1)
            gw = x1 - x0 + 1
        top = max(0, r_end - gh + 1)
        box = a[top:r_end + 1, x0:x1 + 1]
        if box.size == 0 or box.mean() < dark_floor:
            return None                       # 黑屏/淡入淡出：让调用方重试，别拿它下结论
        im = Image.fromarray(box.astype(np.uint8)).resize((640, 480), Image.LANCZOS)
        im.save(out)
    return out


if __name__ == '__main__':
    print(grab_canonical(sys.argv[1] if len(sys.argv) > 1 else '/tmp/_canon.png'))
