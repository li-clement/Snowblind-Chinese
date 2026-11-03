# -*- coding: utf-8 -*-
"""Xbox XBE reverse-engineering helper for default.xbe (BGDA USA)."""
import struct, os
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

XBE = '/Users/lee/code/iso/[XBOX].Baldur\'s.Gate.Dark.Alliance.[USA]/default.xbe'
b = open(XBE, 'rb').read()
SIZE = len(b)

def find_sections(b):
    """XBE section table: stride 0x38 entries starting where .text name-ptr is referenced."""
    i = b.find(b'.text\x00')
    if i < 0: return []
    nameva = 0x10000 + i
    base = b.find(__import__('struct').pack('<I', nameva)) - 0x14
    ents = []
    for k in range(64):
        o = base + k*0x38
        flags, va, vsize, raw, rawsize, nptr = __import__('struct').unpack_from('<6I', b, o)
        if va == 0 and flags == 0: break
        nm = ''
        if nptr:
            s = nptr - 0x10000
            e = b.find(b'\x00', s)
            nm = b[s:e].decode('latin1', 'replace')
        ents.append((flags, va, vsize, raw, rawsize, nm))
    return ents

SECS = find_sections(b)

BASE = 0x10000
def va2raw(va):
    for fl, sv, ss, sr, ssz, nm in SECS:
        if sv <= va < sv + max(ss, 0x1000):
            o = sr + (va - sv)
            if 0 <= o < len(b): return o
    o = va - BASE
    return o if 0 <= o < len(b) else None

def raw2va(off):
    for fl, sv, ss, sr, ssz, nm in SECS:
        if sr <= off < sr + max(ssz, ss, 0x1000):
            return sv + (off - sr)
    return off + BASE

def sec_of(va):
    for fl, sv, ss, sr, ssz, nm in SECS:
        if sv <= va < sv + max(ss, 0x1000):
            return nm or '(anon)'
    return '?'

def read_va(va, n):
    o = va2raw(va)
    return b[o:o+n] if o is not None else b''

_md = Cs(CS_ARCH_X86, CS_MODE_32)
_md.detail = True
def disasm(va, n=0x200, stop_at_ret=False):
    data = read_va(va, n)
    out = []
    for ins in _md.disasm(data, va):
        out.append(ins)
        if stop_at_ret and ins.mnemonic in ('ret','jmp') and len(out) > 4:
            # keep going a bit past unconditional jmp? stop at ret only
            if ins.mnemonic == 'ret': break
    return out

def show(va, n=0x200, stop_at_ret=False):
    for ins in disasm(va, n, stop_at_ret):
        print(f"  0x{ins.address:06X}: {ins.mnemonic:<8s} {ins.op_str}")

def func_start(va, maxback=0x4000):
    o = va2raw(va)
    if o is None: return None
    s = o
    while s > 0 and o - s < maxback:
        if b[s] == 0xCC:
            s -= 1; continue
        if b[s] == 0x90 and b[s-1] == 0x90:
            t = s
            while t > 0 and b[t] == 0x90: t -= 1
            return raw2va(t+1)
        # a preceding int3 pad: found first non-CC byte after CC run handled above;
        # detect function prologue heuristics
        if b[s-1] == 0xCC:
            return raw2va(s)
        s -= 1
    return raw2va(o)

def find_str(s, enc='utf-16le'):
    if enc == 'utf-16le':
        pat = s.encode('utf-16le')
    else:
        pat = s.encode('latin1')
    res = []
    pos = 0
    while True:
        i = b.find(pat, pos)
        if i < 0: break
        res.append(raw2va(i)); pos = i+1
    return res

def xrefs_to(va):
    """Byte search for imm32 references (push/mov/lea/cmp) to a VA."""
    imm = struct.pack('<I', va)
    hits = []
    pos = 0
    while True:
        i = b.find(imm, pos)
        if i < 0: break
        hits.append(raw2va(i)); pos = i+1
    return hits

def imm_scan(value):
    """All absolute VA/immediate occurrences of a value, decoded in context."""
    out = []
    pat = struct.pack('<I', value)
    pos = 0
    while True:
        i = b.find(pat, pos)
        if i < 0: break
        out.append((raw2va(i), b[max(0,i-3):i+6].hex(' ')))
        pos = i+1
    return out

def find_rel_calls(target_va):
    """Find E8 rel32 calls whose destination == target_va."""
    res = []
    for i in range(0x1000, len(b)-5):
        if b[i] == 0xE8:
            rel = struct.unpack_from('<i', b, i+1)[0]
            va = raw2va(i)
            if va is None: continue
            dst = va + 5 + rel
            if dst == target_va:
                res.append(va)
    return res
