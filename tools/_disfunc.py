#!/usr/bin/env python3
# _disfunc.py - find function start via int3 padding, disassemble linearly
# usage: python _disfunc.py <va-in-func> <len>
import struct, sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

XBE = r"E:\Game\ps5\iso\[XBOX].Baldur's.Gate.Dark.Alliance.[USA]\default.xbe"
TEXT_VA, TEXT_RAW, TEXT_SIZE = 0x11000, 0x1000, 0xDC79C
b = open(XBE, 'rb').read()
text = b[TEXT_RAW:TEXT_RAW + TEXT_SIZE]
md = Cs(CS_ARCH_X86, CS_MODE_32)

# string names for annotation
STRINGS = {}
def add(va, nm):
    off = TEXT_RAW + (va - TEXT_VA)
    if 0 <= off < len(text):
        STRINGS[va] = nm
add(0x13ED98, 'font.lmp'); add(0x13ED88, 'gamefonta.fnt'); add(0x13ED78, 'gamefontmed.fnt')
add(0x13ED64, 'gamefontsmall.fnt'); add(0x13ED58, 'gtext.lmp')
add(0x14038C, 'frontend.lmp'); add(0x140520, 'creditfont.fnt'); add(0x140550, 'bigfont.fnt')
# other known strings from earlier scans
for va in (0x13E858, 0x13E84C, 0x13EDD0, 0x13EDCC, 0x13EDD4):
    add(va, '??')

def find_func_start(va):
    off = TEXT_RAW + (va - TEXT_VA)
    s = off - 1
    while s > 0 and s > off - 0x8000:
        if text[s] == 0xCC:
            s -= 1
            continue
        # first non-CC after padding: the byte before must have been part of run
        if s + 1 < len(text) and text[s + 1] == 0xCC:
            return TEXT_VA + (s - TEXT_RAW) + 1
        s -= 1
    return None

def disasm(start_va, nbytes):
    off = TEXT_RAW + (start_va - TEXT_VA)
    code = text[off:off + nbytes]
    print(f"===== func @0x{start_va:X} (len {nbytes:#x}) =====")
    for ins in md.disasm(code, start_va):
        op = ins.op_str
        extra = ''
        if ins.mnemonic == 'call':
            try:
                tgt = int(op, 16)
                extra = f"  ; -> 0x{tgt:X}"
            except ValueError:
                pass
        elif ins.mnemonic.startswith('j') and ins.mnemonic not in ('jmp', 'je'):
            try:
                tgt = int(op, 16)
                extra = f"  ; -> 0x{tgt:X}"
            except ValueError:
                pass
        elif ins.mnemonic == 'push' or ins.mnemonic == 'mov':
            try:
                v = int(op.split()[-1], 16)
                if v in STRINGS:
                    extra = f"  ; <{STRINGS[v]}>"
            except (ValueError, IndexError):
                pass
        print(f"  0x{ins.address:06X}: {ins.mnemonic:<8s} {op}{extra}")

anchor = int(sys.argv[1], 16)
n = int(sys.argv[2], 16)
fs = find_func_start(anchor)
if fs is None:
    # fallback: scan back for 0xCC then look for prologue
    print("no int3 padding found")
    sys.exit(1)
print(f"[func start of 0x{anchor:X} = 0x{fs:X}]")
disasm(fs, n)