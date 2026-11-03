#!/usr/bin/env python3
"""中文串半角标点 → 全角（文本侧）

为什么能原地改：游戏 .uni 文本是 **UTF-16LE**（已实测：中文台词按 utf-16-le 能在 res/*.gob 里定位），
而 `,? !:;` 与 `，？！：；` 都是 1 个码元 = 2 字节，替换**等长** → 不动容器长度、不动 0x80 对齐、
不需要重建 .lmp/.gob，只要回封 ISO。

安全边界（三条，全是硬门槛，不满足就跳过并报告）：
1. 只改 zh_*.uni.json 里我们自己写的译文——按「旧字符串的 UTF-16LE 字节」在 .gob 里定位，
   绝不盲搜盲改，避免动到原版英文文本或二进制数据。
2. 千分位不动：`,` 两侧都是数字（2,000）时跳过。
3. 占位符不动：%d %s %% %f 本身不含这五个符号，转换不触碰 % 序列。

用法：
  python3 tools/punct_fullwidth.py --dry                # 只统计
  python3 tools/punct_fullwidth.py --apply-json         # 改 translation/zh_*.uni.json（留 .bak）
  python3 tools/punct_fullwidth.py --patch-tree         # 改解包树 res/*.gob（留 .punctbak）
  python3 tools/punct_fullwidth.py --coverage           # 检查新字符在字体里有没有字形
"""
import argparse, collections, glob, json, os, re, shutil, struct, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TREE = os.path.join(BASE, "[XBOX].Baldur's.Gate.Dark.Alliance.[USA]")
MAP = {',': '，', '?': '？', '!': '！', ':': '：', ';': '；'}
CJK = re.compile(r'[\u3000-\u303f\u4e00-\u9fff\uff00-\uffef]')
# 「中文语境」的邻居不止汉字：—— 、“” ‘’ … 这些标点同样说明这半句是中文
CJKISH = re.compile(r'[\u2010-\u206f\u3000-\u303f\u4e00-\u9fff\uff00-\uffef]')
# printf 占位符：判断前邻时要先把它跳掉，否则「存档 %d?」会因为紧邻 'd' 而漏转
PLACE = re.compile(r'%[-#0-9.]*[a-zA-Z%]$')


def _prev(s, i):
    j = i
    while True:
        m = PLACE.search(s[:j])
        if not m:
            return s[j - 1] if j else ''
        j = m.start()


def convert(s):
    """返回 (新串, 改动的 [(旧字符, 位置)] , 跳过的 [(旧字符, 原因)])"""
    out, done, skipped = [], [], []
    if not CJK.search(s):                     # 纯英文串一个字符都不碰
        return s, [], [(',', '整串无中文')] * sum(s.count(c) for c in MAP)
    for i, ch in enumerate(s):
        if ch not in MAP:
            out.append(ch)
            continue
        prev = _prev(s, i)
        nxt = s[i + 1] if i + 1 < len(s) else ''
        if ch == ',' and prev.isdigit() and nxt.isdigit():
            skipped.append((ch, '千分位'))
            out.append(ch)
            continue
        if ch in '%:!;' and prev == '%':          # 理论上不会出现，防御性保住 % 序列
            skipped.append((ch, '%序列'))
            out.append(ch)
            continue
        if not (CJKISH.match(prev) or CJKISH.match(nxt) or (nxt == '' and CJK.search(s))):
            skipped.append((ch, '两侧都非中文'))
            out.append(ch)                        # 纯英文/代码串不动
            continue
        out.append(MAP[ch])
        done.append(ch)
    return ''.join(out), done, skipped


def load_pairs():
    for p in sorted(glob.glob(os.path.join(BASE, 'translation', 'zh_*.uni.json'))):
        d = json.load(open(p, encoding='utf-8-sig'))
        yield p, d


def cmd_dry():
    n_str = n_ch = 0
    per = collections.Counter()
    skip = collections.Counter()
    for p, d in load_pairs():
        for k, v in d.items():
            nv, done, skipped = convert(str(v))
            n_str += 1 if done else 0
            n_ch += len(done)
            per.update(done)
            skip.update(f'{a}/{b}' for a, b in skipped)
    print(f'要改的条目 {n_str} 条，共 {n_ch} 个标点：' +
          '  '.join(f'{a}→{MAP[a]}×{n}' for a, n in per.most_common()))
    print('跳过:', dict(skip) or '无')


def cmd_apply_json():
    changed = 0
    for p, d in load_pairs():
        dirty = False
        for k, v in list(d.items()):
            nv, done, _ = convert(str(v))
            if done:
                d[k] = nv
                dirty = True
        if dirty:
            bak = p + '.bak'
            if not os.path.exists(bak):
                shutil.copy2(p, bak)
            json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
            changed += 1
    print(f'已改写 {changed} 个 json（原件在同名 .bak）')


def old_new_pairs():
    """从 .bak（改动前）与当前 json（改动后）取出需要落树的字节对"""
    for p, d in load_pairs():
        bak = p + '.bak'
        if not os.path.exists(bak):
            continue
        o = json.load(open(bak, encoding='utf-8-sig'))
        for k, v in d.items():
            ov = str(o.get(k, ''))
            nv = str(v)
            if ov == nv or len(ov) != len(nv):
                continue
            yield k, ov.encode('utf-16-le'), nv.encode('utf-16-le')


def cmd_patch_tree():
    pairs = [(k, a, b) for k, a, b in old_new_pairs() if len(a) == len(b)]
    # 台词在 res/*.gob，菜单/配置串在 res/gtext.lmp —— 两类都要扫
    pats = [('res', '*.gob'), ('res', '*.lmp'),
            ('res', os.path.join('**', '*.gob')), ('res', os.path.join('**', '*.lmp'))]
    # 坑：目录名里的 [XBOX] 会被 glob 当成字符集合，必须转义（open() 不受影响）
    root = glob.escape(TREE)
    gobs = sorted(set().union(*[set(glob.glob(os.path.join(root, *pt))) for pt in pats]))
    total = touched = 0
    found_keys = set()
    for g in gobs:
        data = bytearray(open(g, 'rb').read())
        n = 0
        for k, a, b in pairs:
            start = 0
            while True:
                i = data.find(a, start)
                if i < 0:
                    break
                data[i:i + len(b)] = b          # 等长替换：容器长度与 0x80 对齐都不变
                found_keys.add(k)
                n += 1
                start = i + len(a)
        if n:
            bak = g + '.punctbak'
            if not os.path.exists(bak):
                shutil.copy2(g, bak)            # 只给真正动过的文件留底
            open(g, 'wb').write(bytes(data))
            total += n
            touched += 1
    missing = [k for k, _, _ in pairs if k not in found_keys]
    print(f'扫描 {len(gobs)} 个 .gob/.lmp，动过 {touched} 个，共替换 {total} 处')
    print(f'树里一条都没找到的译文条目 {len(missing)} 条'
          + ('（多半是菜单/配置串住在 .lmp 而不是 .gob，用 --coverage 复核）' if missing else ''))
    if missing:
        print('  例:', ', '.join(missing[:8]))


def font_codes():
    """res/font.lmp + res/frontend.lmp 里所有 .fnt 字表的 code 集合（含共享薄头指向的 master）"""
    codes = set()
    for nm in ('res/font.lmp', 'res/frontend.lmp'):
        p = os.path.join(TREE, nm)   # open() 不需要 glob.escape
        b = open(p, 'rb').read()
        for i in range(struct.unpack_from('<I', b, 0)[0]):
            q = 4 + i * 64
            if not b[q:q + 56].split(b'\0')[0].decode('latin1', 'replace').endswith('.fnt'):
                continue
            off, sz = struct.unpack_from('<II', b, q + 56)
            cnt, rec = struct.unpack_from('<H', b, off)[0], struct.unpack_from('<I', b, off + 8)[0]
            rp = (off + rec) & 0xFFFFFFFF
            if rp + cnt * 16 > len(b):
                continue
            for j in range(cnt):
                codes.add(struct.unpack_from('<H', b, rp + j * 16)[0])
    return codes


def cmd_coverage():
    need = set()
    for p, d in load_pairs():
        for v in d.values():
            need |= {c for c in str(v) if CJK.match(c)}
    have = font_codes()
    miss = sorted(c for c in need if ord(c) not in have)
    print(f'译文用到的 CJK/全角字符 {len(need)} 种，字体里有 {len(need) - len(miss)} 种')
    if miss:
        print('!! 缺字形（会画成空白/豆腐）:', ' '.join(f'{c}=U+{ord(c):04X}' for c in miss))
        print('   → 把缺的字符加进 translation/jobs/zh_punct.txt 再重跑构建')
        return 1
    print('全部有字形 ✅')
    return 0


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--dry', action='store_true')
    g.add_argument('--apply-json', action='store_true')
    g.add_argument('--patch-tree', action='store_true')
    g.add_argument('--coverage', action='store_true')
    a = ap.parse_args()
    if a.dry:
        cmd_dry()
    elif a.apply_json:
        cmd_apply_json()
    elif a.patch_tree:
        cmd_patch_tree()
    else:
        sys.exit(cmd_coverage())
