#!/usr/bin/env python3
# quick punctuation / charset analysis for zh translations
import json, glob, os

punct = {}
tot_ascii_punct = 0
tot_full_punct = 0
nkeys = 0
for f in glob.glob(r'E:\Game\ps5\iso\translation\zh_*.json'):
    obj = json.load(open(f, encoding='utf-8'))
    nkeys += len(obj)
    for k, v in obj.items():
        for ch in v:
            o = ord(ch)
            if 0x20 <= o < 0x7F:
                if ch in '.,!?;:\'"()-':
                    punct['ASCII:' + ch] = punct.get('ASCII:' + ch, 0) + 1
                    tot_ascii_punct += 1
            elif 0x3000 <= o <= 0x303F or 0xFF00 <= o <= 0xFFEF:
                tot_full_punct += 1
                punct['FW:' + ch] = punct.get('FW:' + ch, 0) + 1

print('total keys:', nkeys)
print('ASCII punct count:', tot_ascii_punct)
print('fullwidth punct count:', tot_full_punct)
for k, v in sorted(punct.items(), key=lambda x: -x[1])[:40]:
    print(f'  {k!r}: {v}')

cs = open(r'E:\Game\ps5\iso\translation\jobs\zh_charset.txt', encoding='utf-8').read()
chars = [c for c in cs if c not in '\n\r\t']
print('\ncharset raw len:', len(cs), 'unique:', len(set(chars)))
ascii_chars = sorted({c for c in chars if 0x20 <= ord(c) < 0x7F})
cj = sorted({c for c in chars if ord(c) >= 0x2E80})
print('charset ASCII subset:', ascii_chars)
print('charset CJK count:', len(cj), 'first 60:', ''.join(cj[:60]))