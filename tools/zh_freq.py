# -*- coding: utf-8 -*-
# v11 prep: collect ALL translated zh text, compute char frequency (hanzi only)
import json, os, re
from collections import Counter

BASE = r'E:\Game\ps5\iso\translation'
texts = []
for fn in os.listdir(BASE):
    if fn.startswith('zh_') and fn.endswith('.uni.json'):
        try:
            d = json.load(open(os.path.join(BASE, fn), encoding='utf-8'))
        except Exception as e:
            print('skip', fn, e)
            continue
        def walk(o):
            if isinstance(o, dict):
                for v in o.values():
                    walk(v)
            elif isinstance(o, list):
                for v in o:
                    walk(v)
            elif isinstance(o, str):
                texts.append(o)
        walk(d)
# also gtext full and all_text jsons
for fn in ('gtext_uni_full.txt', 'all_text_v2.json'):
    p = os.path.join(BASE, fn)
    if not os.path.exists(p):
        continue
    try:
        raw = open(p, encoding='utf-8').read()
    except Exception as e:
        print('skip', fn, e)
        continue
    if fn.endswith('.json'):
        try:
            d = json.loads(raw)
            def walk(o):
                if isinstance(o, dict):
                    for v in o.values(): walk(v)
                elif isinstance(o, list):
                    for v in o: walk(v)
                elif isinstance(o, str):
                    texts.append(o)
            walk(d)
        except Exception as e:
            texts.append(raw)
    else:
        texts.append(raw)

alltext = '\n'.join(texts)
cjk = [ch for ch in alltext if '\u4e00' <= ch <= '\u9fff']
cnt = Counter(cjk)
print('hanzi distinct:', len(cnt), ' total:', len(cjk))
top = [c for c, _ in cnt.most_common(860)]
# how many needed to cover 90%/95%/99% of chars
tot = len(cjk)
for frac in (0.90, 0.95, 0.99):
    run = 0
    for i, (_, n) in enumerate(cnt.most_common()):
        run += n
        if run >= tot * frac:
            print(f'{frac:.0%} coverage needs {i+1} chars (of {len(cnt)})')
            break
top860 = ''.join(c for c, _ in cnt.most_common(860))
open(os.path.join(BASE, 'jobs', 'zh_top860.txt'), 'w', encoding='utf-8').write(top860)
print('saved zh_top860.txt (860 chars)')
top1100 = ''.join(c for c, _ in cnt.most_common(1100))
open(os.path.join(BASE, 'jobs', 'zh_top1100.txt'), 'w', encoding='utf-8').write(top1100)
print('saved zh_top1100.txt (1100 chars)')
top1502 = ''.join(c for c, _ in cnt.most_common(1502))
open(os.path.join(BASE, 'jobs', 'zh_top1502.txt'), 'w', encoding='utf-8').write(top1502)
print('saved zh_top1502.txt (1502 chars)')