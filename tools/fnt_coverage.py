#!/usr/bin/env python3
# fnt_coverage.py - check japfont coverage of zh charset + dump section tables
import struct, os

ANALYSIS = r'E:\Game\ps5\iso\analysis'
TR = r'E:\Game\ps5\iso\translation'

def load(path):
    b = open(path, 'rb').read()
    cnt, hgt = struct.unpack_from('<HH', b, 0)
    nsect, magic, offSec, offBmp = struct.unpack_from('<IIII', b, 4)
    atw, ath = struct.unpack_from('<HH', b, offBmp)
    start = offBmp + 1080
    recStart = offSec - cnt * 16
    recs = {}
    for i in range(cnt):
        o = recStart + i * 16
        vals = struct.unpack_from('<8H', b, o)
        if vals[0] != 0xFFFF:
            recs[vals[0]] = vals
    return dict(b=b, cnt=cnt, hgt=hgt, nsect=nsect, magic=magic, offSec=offSec,
                offBmp=offBmp, atw=atw, ath=ath, start=start, recStart=recStart, recs=recs)

# 1) section tables
for fn in ['gamefonta.fnt', 'japfontbig0.fnt', 'japfontsmall0.fnt', 'bigfont.fnt']:
    f = load(os.path.join(ANALYSIS, fn))
    print(f"== {fn}: cnt={f['cnt']} nsect={f['nsect']} offSec=0x{f['offSec']:X} recStart=0x{f['recStart']:X}")
    for s in range(f['nsect']):
        o = f['offSec'] + s * 12
        a, b2, c = struct.unpack_from('<3I', f['b'], o)
        print(f"   sect[{s}] @0x{o:X}: {a} {b2} {c}  (hex: {f['b'][o:o+12].hex()})")
    tail = f['b'][f['offSec'] + f['nsect'] * 12: f['offSec'] + f['nsect'] * 12 + 24]
    print(f"   after last sect: {tail.hex()}")

# 2) japfont coverage of zh charset
charset = open(os.path.join(TR, 'jobs', 'zh_charset.txt'), encoding='utf-8').read()
chars = list(charset)
for fn in ['japfontbig0.fnt', 'japfontsmall0.fnt']:
    f = load(os.path.join(ANALYSIS, fn))
    hav = [c for c in chars if ord(c) in f['recs']]
    miss = [c for c in chars if ord(c) not in f['recs']]
    print(f"\n{fn}: {len(chars)} chars in charset, {len(hav)} covered, {len(miss)} missing")
    print(f"   missing sample: {''.join(miss[:80])}")
    print(f"   missing count: {len(miss)}")
    if miss:
        # which ranges?
        from collections import Counter
        ranges = Counter()
        for c in miss:
            o = ord(c)
            if 0x20 <= o <= 0x7E: ranges['ASCII'] += 1
            elif 0x3000 <= o <= 0x30FF: ranges['kana'] += 1
            elif 0x4E00 <= o <= 0x9FFF: ranges['CJK'] += 1
            else: ranges[f'U+{o:04X}'] += 1
        print(f"   missing by range: {dict(ranges)}")