#!/usr/bin/env python3
"""让 xemu 用 F12 导出 *纯游戏帧*（不受桌面遮挡），逐个 ISO 取样。

用法: python3 f12_shot.py <iso> <out.png> [wait=48] [frames=2]
原理: 改写 toml 的 dvd_path → 启动 → 等待 → 激活 xemu 窗口 → System Events key code 111(F12)
      xemu 会把 640x480 原始帧存到 ISO 同级目录 xemu-YYYY-MM-DD-HH-MM-SS.png
"""
import os, re, shutil, subprocess, sys, time

XEMU = '/Users/lee/game/xemu-0.8.139-macos-universal/xemu.app/Contents/MacOS/xemu'
TOML = os.path.expanduser('~/Library/Application Support/Xemu/xemu/xemu.toml')
ISO_DIR = '/Users/lee/code/iso'


def set_dvd(iso):
    s = open(TOML).read()
    s2 = re.sub(r"dvd_path = '[^']*'", f"dvd_path = '{iso}'", s)
    open(TOML, 'w').write(s2)
    assert f"dvd_path = '{iso}'" in open(TOML).read()


def newest_shot(since):
    best, bt = None, since
    for fn in os.listdir(ISO_DIR):
        if fn.startswith('xemu-') and fn.endswith('.png'):
            p = os.path.join(ISO_DIR, fn)
            m = os.path.getmtime(p)
            if m > bt:
                best, bt = p, m
    return best


def main():
    iso = os.path.abspath(sys.argv[1])
    out = os.path.abspath(sys.argv[2])
    wait = float(sys.argv[3]) if len(sys.argv) > 3 else 48.0
    frames = int(sys.argv[4]) if len(sys.argv) > 4 else 2
    subprocess.run(['pkill', '-9', '-f', 'MacOS/xemu'], capture_output=True)
    time.sleep(2)
    set_dvd(iso)
    t0 = time.time()
    log = open('/tmp/xemu_shot_run.log', 'w')
    subprocess.Popen([XEMU], stdout=log, stderr=subprocess.STDOUT)
    time.sleep(wait)
    pid = subprocess.run(['pgrep', '-f', 'MacOS/xemu'], capture_output=True, text=True).stdout.split()
    if not pid:
        print('!! xemu 没起来'); return
    subprocess.run(['osascript', '-e',
                    f'tell application "System Events" to set frontmost of (first process whose unix id is {pid[0]}) to true'],
                   capture_output=True)
    time.sleep(1.5)
    shots = []
    tries = 0
    while len(shots) < frames and tries < frames * 4:
        tries += 1
        subprocess.run(['osascript', '-e',
                        f'tell application "System Events" to set frontmost of (first process whose unix id is {pid[0]}) to true'],
                       capture_output=True)
        time.sleep(1.0)
        subprocess.run(['osascript', '-e', 'tell application "System Events" to key code 111'], capture_output=True)
        time.sleep(2.0)
        p = newest_shot(t0)
        if p and p not in shots:
            shots.append(p)
    for i, p in enumerate(shots):
        d = out if i == 0 else re.sub(r'\.png$', f'_f{i+1}.png', out)
        shutil.copy(p, d)
        print(f'  saved {d}   (src {os.path.basename(p)}, {os.path.getsize(p)}B)')
    if not shots:
        print('!! 没拿到 F12 截图，检查 xemu 是否聚焦/权限')
    subprocess.run(['pkill', '-9', '-f', 'MacOS/xemu'], capture_output=True)


main()
