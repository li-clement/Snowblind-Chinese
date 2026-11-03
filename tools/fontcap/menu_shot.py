#!/usr/bin/env python3
"""可靠版启动/取证：改 dvd_path → 启 xemu → 轮询到主菜单 → 按窗口ID抓帧 → 关模拟器
   判据：主菜单 = 全屏ink<45000(暗背景) 且 四条菜单条区ink>2500"""
import os, re, subprocess, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image
import numpy as np
from wingrab import grab

XEMU = '/Users/lee/game/xemu-0.8.139-macos-universal/xemu.app/Contents/MacOS/xemu'
TOML = os.path.expanduser('~/Library/Application Support/Xemu/xemu/xemu.toml')
ISO_DIR = '/Users/lee/code/iso'
# 底部 "Ⓐ 确认"：实测真包围盒 y419..437 / x295..350。
# 不能沿用 y400..442/x270..390 —— 那会把第四条菜单条左下角的金色装饰(y407,x245..272)
# 和 16px 的第四项文字一起框进来，造成 130~190 的假阳性读数（曾据此误判过两次）。
PROMPT = (413, 447, 285, 362)   # 16px 时字形更宽高，框要留余量
BARS = (275, 410, 215, 425)        # 四条菜单条
ORIENT = (245, 275, 390, 425)      # 对齐基准：菜单条左下金色装饰


def ink(a, box=None, dy=0):
    x0, x1, y0, y1 = box or (0, 640, 0, 480)
    return int((a[y0 + dy:y1 + dy, x0:x1] > 60).sum())


def align_dy(a):
    """窗口抓帧的裁剪上边界是推算的，会有十几像素整体偏移。
       用菜单条左下金色装饰所在行对齐（标准帧里在 y407）。"""
    x0, x1, y0, y1 = ORIENT
    return 407 - (int(a[y0:y1, x0:x1].sum(axis=1).argmax()) + y0)


def is_menu(a):
    return ink(a) < 60000 and ink(a, BARS) > 500


def ascii_prompt(a, dy=0):
    """提示会呼吸/闪烁，像素计数不可靠（同一状态能读出 42~885）。
       最终判据 = 这一段字符图里有没有「Ⓐ 圆环 + 两个汉字」，肉眼/视觉模型一眼可判。"""
    lines = []
    for r in range(412 + dy, 448 + dy, 2):
        line = ''.join('#' if a[r, c:c + 2].max() > 55 else '.' for c in range(250, 400, 2))
        if '#' in line:
            lines.append(f'  y{r:3d} {line}')
    return '\n'.join(lines)


def report(p, iso='', ascii_dump=False):
    a = np.asarray(Image.open(p), dtype=np.uint8).astype(int)
    dy = align_dy(a)
    pr = int(a[PROMPT[0] + dy:PROMPT[1] + dy, PROMPT[2]:PROMPT[3]].max())   # 峰值亮度，抗闪烁
    if ascii_dump:
        print(ascii_prompt(a, dy))
    return (f'{os.path.basename(p):20s}[{iso:22s}] 全屏ink={ink(a):6d} dy={dy:3d} '
            f'菜单条ink={ink(a, BARS, dy):5d} ' +
            (f'提示峰值={pr:3d} → ' + ('存在 ✅' if pr > 75 else '缺失 ❌') if is_menu(a) else '未到菜单 ⚠️'))


def run(iso, out, budget=150):
    subprocess.run(['pkill', '-9', '-f', 'MacOS/xemu'], capture_output=True)
    time.sleep(2)
    s = open(TOML).read()
    # 只替换已有的那一条；绝不追加（重复键会让 xemu 直接拒绝启动）
    assert re.search(r"^dvd_path = ", s, re.M), 'xemu.toml 里没有 dvd_path，先手工加一条'
    open(TOML, 'w').write(re.sub(r"^dvd_path = .*", f"dvd_path = '{ISO_DIR}/{iso}'", s, count=1, flags=re.M))
    with open('/tmp/xemu_run.log', 'w') as lg:
        subprocess.Popen([XEMU], stdout=lg, stderr=subprocess.STDOUT)
    time.sleep(35)
    t0 = time.time()
    while time.time() - t0 < budget:
        grab('/tmp/_probe.png')
        a = np.asarray(Image.open('/tmp/_probe.png'), dtype=np.uint8)
        if is_menu(a):
            time.sleep(4)
            grab(out)
            subprocess.run(['pkill', '-9', '-f', 'MacOS/xemu'], capture_output=True)
            return out
        time.sleep(3)
    grab(out)
    subprocess.run(['pkill', '-9', '-f', 'MacOS/xemu'], capture_output=True)
    return out


if __name__ == '__main__':
    for iso, out in ((a.split('=')) for a in sys.argv[1:]):
        print(report(run(iso, out), iso))
