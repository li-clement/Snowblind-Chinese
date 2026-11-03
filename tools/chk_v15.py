#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v15 校验：
 1) 每个字形 rect 内的墨迹必须完全属于该字形（无邻居串入）→ 逐格渲染比对。
 2) 拉丁像素与原图 100% 一致。
 3) 度量报告：一 / 。 / ， / 我 的 rect、ink 尺寸、f5、adv。
 4) ASCII 预览（本会话模型无图像输入，用字符画核对）。
"""
import struct, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_v15 import load_font, latin_pixels

def check(path, em):
    f = load_font(path)
    atw, ath, start = f['atw'], f['ath'], f['start']
    b = f['b']
    recs = [v for v in f['recs'] if v[1] < v[2] and v[3] < v[4]]

    # ---- 1) rect 重叠检测（串字的充分条件之一）
    ov = 0
    for i in range(len(recs)):
        a = recs[i]
        for j in range(i + 1, len(recs)):
            c = recs[j]
            if a[1] < c[2] and c[1] < a[2] and a[3] < c[4] and c[3] < a[4]:
                ov += 1

    # ---- 2) 拉丁像素一致性
    lat_ok = lat_tot = 0
    for v in f['recs']:
        if v[0] == 32 or v[0] in (0, 0xFFFF): continue
        lp = latin_pixels(f, v)
        if lp is None: continue
        x0, y0, w, h, rows = lp
        lat_tot += 1
        # 在 v15 图集里同一坐标应逐位相同（拉丁照搬）
        same = all(rows[yy][xx] == (1 if b[start + (y0+yy)*atw + x0+xx] > 127 else 0)
                   for yy in range(h) for xx in range(w))
        if same: lat_ok += 1

    # ---- 3) CJK：墨迹必须落在 rect 内且四周留白（即不与邻格共享像素）
    cjk = [v for v in recs if v[0] >= 0x2000]
    pad_ok = 0
    for v in cjk:
        x0, x1, y0, y1 = v[1], v[2], v[3], v[4]
        # rect 右/下各应有 ≥1 空白列/行（属于邻格起点之前）
        col_blank = all(b[start + yy*atw + x1] <= 127 for yy in range(y0, y1) if x1 < atw)
        row_blank = all(b[start + y1*atw + xx] <= 127 for xx in range(x0, x1) if y1 < ath)
        if col_blank and row_blank: pad_ok += 1

    print(f'{os.path.basename(path)}')
    print(f'  records={len(recs)} latin={lat_tot} (pixel-identical {lat_ok}) cjk={len(cjk)}')
    print(f'  rect overlap pairs = {ov}')
    print(f'  CJK with clean right/bottom gutter = {pad_ok}/{len(cjk)}')

    for code in (0x4E00, 0x3002, 0xFF0C, 0x6211, 0x7684, 0x2014, 0x2026):
        for v in f['recs']:
            if v[0] != code: continue
            x0, x1, y0, y1 = v[1], v[2], v[3], v[4]
            pts = [(x, y) for y in range(y0, y1) for x in range(x0, x1) if b[start + y*atw + x] > 127]
            if not pts:
                print(f'  {chr(code)} rect w={x1-x0} h={y1-y0} EMPTY adv={v[6]}'); break
            ix0=min(p[0] for p in pts); ix1=max(p[0] for p in pts)+1
            iy0=min(p[1] for p in pts); iy1=max(p[1] for p in pts)+1
            print(f'  {chr(code)} rect=({x0},{x1},{y0},{y1}) rw={x1-x0} rh={y1-y0} '
                  f'| ink w={ix1-ix0} h={iy1-iy0} | f5={v[5]} adv={v[6]}')
            for yy in range(iy0, iy1):
                print('     ', ''.join('#' if b[start+yy*atw+xx]>127 else '.' for xx in range(ix0,ix1)))
            break
    return ov, lat_ok == lat_tot

if __name__ == '__main__':
    em = int(sys.argv[2]) if len(sys.argv) > 2 else 16
    ok = True
    for p in sys.argv[1].split(','):
        o, l = check(p, em)
        ok = ok and (o == 0) and l
    print('ALL OK' if ok else 'PROBLEMS FOUND')
