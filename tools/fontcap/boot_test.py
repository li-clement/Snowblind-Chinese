#!/usr/bin/env python3
"""xemu 启动验证：杀掉残留实例 → 启动指定 ISO → 等待 → 截图 → 统计亮度。

用法: python3 boot_test.py <iso> [secs=55] [out.png]
判据(与历史轮次一致): 标题/菜单正常 mean≈26~40, frac>25≈0.4; 黑屏 mean≈5, frac>25≈0
"""
import os, subprocess, sys, time, glob

XEMU = '/Users/lee/game/xemu-0.8.139-macos-universal/xemu.app/Contents/MacOS/xemu'


def kill_all():
    subprocess.run(['pkill', '-9', '-f', 'MacOS/xemu'], capture_output=True)
    time.sleep(2.0)
    subprocess.run(['pkill', '-9', '-f', 'qemu-system'], capture_output=True)
    time.sleep(1.0)


def shoot(path):
    subprocess.run(['screencapture', '-x', path], check=True)


def stats(path):
    from PIL import Image
    im = Image.open(path).convert('L')
    w, h = im.size
    im = im.crop((w // 5, h // 6, w * 4 // 5, h * 5 // 6))   # 去掉屏幕黑边/桌面
    px = list(im.getdata())
    n = len(px)
    mean = sum(px) / n
    frac = sum(1 for v in px if v > 25) / n
    return mean, frac, max(px)


TOML = os.path.expanduser('~/Library/Application Support/Xemu/xemu/xemu.toml')


def set_dvd(iso):
    s = open(TOML).read()
    import re
    s2 = re.sub(r"dvd_path = '[^']*'", f"dvd_path = '{iso}'", s)
    open(TOML, 'w').write(s2)
    return s


def inkstats(path):
    """画面中心区域亮墨比例（字号变大 → 该值明显上升）"""
    from PIL import Image
    im = Image.open(path).convert('L')
    w, h = im.size
    im = im.crop((w // 5, h // 6, w * 4 // 5, h * 5 // 6))
    px = list(im.getdata())
    return sum(1 for v in px if v > 60) / len(px)


def main():
    iso = os.path.abspath(sys.argv[1])
    secs = float(sys.argv[2]) if len(sys.argv) > 2 else 55.0
    out = sys.argv[3] if len(sys.argv) > 3 else '/tmp/xemu_shot.png'
    kill_all()
    orig = set_dvd(iso)
    log = open('/tmp/xemu_run.log', 'w')
    p = subprocess.Popen([XEMU], stdout=log, stderr=subprocess.STDOUT)
    time.sleep(1.0)
    txt = open('/tmp/xemu_run.log').read()
    if f'cdrom,file={iso}' not in txt:
        print('!! xemu 没有挂载目标 ISO，日志中的 cdrom 参数为:')
        for line in txt.splitlines():
            if 'cdrom' in line:
                print('   ', line[:400])
    time.sleep(secs)
    shoot(out)
    m, f, mx = stats(out)
    ink = inkstats(out)
    print(f'{os.path.basename(iso)}: after {secs:.0f}s  mean={m:.1f} frac>25={f:.3f} max={mx} ink={ink:.4f}')
    open(TOML, 'w').write(orig)
    return p


if __name__ == '__main__':
    pr = main()
    time.sleep(0.5)
    kill_all()
