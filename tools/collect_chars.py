#!/usr/bin/env python3
# collect_chars.py - collect all CJK + special chars used in zh translations, for font build
import json, os

TR = r'E:\Game\ps5\iso\translation'
files = ['zh_act1.uni.json', 'zh_act2.uni.json', 'zh_act3.uni.json', 'zh_tavern.uni.json',
         'zh_bthrone_cut.uni.json', 'zh_cuttown_cut.uni.json', 'zh_xantam.uni.json',
         'zh_sewer1_cut.uni.json', 'zh_csewer1_cut.uni.json', 'zh_towert_cut.uni.json',
         'zh_gtext_part1.uni.json', 'zh_gtext_part2.uni.json']

chars = {}
for f in files:
    p = os.path.join(TR, f)
    with open(p, encoding='utf-8') as fh:
        obj = json.load(fh)
    for k, v in obj.items():
        for ch in v:
            chars[ch] = chars.get(ch, 0) + 1

cjk = sorted((c for c in chars if 0x4E00 <= ord(c) <= 0x9FFF), key=ord)
other = sorted((c for c in chars if not (0x4E00 <= ord(c) <= 0x9FFF)), key=ord)
print(f"total unique chars: {len(chars)}")
print(f"CJK chars: {len(cjk)}")
print(f"non-CJK chars: {len(other)}: {''.join(other)}")
with open(os.path.join(TR, 'jobs', 'zh_charset.txt'), 'w', encoding='utf-8') as fh:
    fh.write(''.join(chars.keys()))
print("charset saved -> translation/jobs/zh_charset.txt")