#!/usr/bin/env python3
# fnt_rt.py - roundtrip self-verify a .fnt: header, records, atlas parse; render samples as ASCII
import struct, sys

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
    ok = (len(b) == start + atw * ath)
    print(f"{path}: ok={ok} cnt={cnt} hgt={hgt} nsect={nsect} magic=0x{magic:X} "
          f"offSec=0x{offSec:X} offBmp=0x{offBmp:X} atlas={atw}x{ath} recs={len(recs)} file={len(b)} end={start+atw*ath}")
    return dict(b=b, atw=atw, ath=ath, start=start, recs=recs)

def show(f, ch, w=20):
    o = ord(ch)
    if o not in f['recs']:
        print(f"  {ch!r}: NO REC")
        return
    v = f['recs'][o]
    y, x = v[1], v[2]
    b, atw, ath, start = f['b'], f['atw'], f['ath'], f['start']
    hh = v[4] - v[3] if v[4] > v[3] else 14
    print(f"  {ch!r} U+{o:04X} rec=({v[1]},{v[2]},{v[3]},{v[4]},{v[5]},{v[6]}) @({y},{x}) h={hh}")
    for yy in range(max(0, y), min(y + hh, ath)):
        row = b[start + yy * atw + x: start + yy * atw + x + w]
        s = ''.join('#' if vv > 127 else ('.' if vv > 0 else ' ') for vv in row)
        print(f"    {yy:03d}|{s}|")

if __name__ == '__main__':
    p = sys.argv[1]
    f = load(p)
    for c in ['A', '0', '你', '好', '传', '。']:
        show(f, c)