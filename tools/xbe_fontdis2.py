#!/usr/bin/env python3
# xbe_fontdis2.py - find real function boundaries via int3 padding, disassemble font loader
import struct
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

XBE = r"E:\Game\ps5\iso\[XBOX].Baldur's.Gate.Dark.Alliance.[USA]\default.xbe"
TEXT_VA, TEXT_RAW, TEXT_SIZE = 0x11000, 0x1000, 0xDC79C
b = open(XBE, 'rb').read()
text = b[TEXT_RAW:TEXT_RAW + TEXT_SIZE]
md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True

def find_func_start(va):
    off = TEXT_RAW + (va - TEXT_VA)
    s = off
    while s > 0 and s > off - 0x1000:
        # int3 padding: run of >=2 CC bytes then a non-CC start
        if text[s] == 0xCC:
            s -= 1
            continue
        if s + 1 < len(text) and text[s+1] == 0xCC and text[s] != 0xCC:
            return TEXT_VA + (s - TEXT_RAW) - 1 if text[s-1] == 0xCC else TEXT_VA + (s - TEXT_RAW)
        # also handle 90 90 (nop) padding
        if text[s] == 0x90 and s > 0 and text[s-1] == 0x90:
            # walk back over nops
            t = s
            while t > 0 and text[t] == 0x90:
                t -= 1
            if t < s - 3:
                return TEXT_VA + (t + 1 - TEXT_RAW)
        s -= 1
    return TEXT_VA + (off - TEXT_RAW)

def disasm_linear(start_va, nbytes, label=""):
    off = TEXT_RAW + (start_va - TEXT_VA)
    print(f"\n===== {label} @0x{start_va:X} =====")
    code = text[off:off + nbytes]
    for ins in md.disasm(code, start_va):
        print(f"  0x{ins.address:06X}: {ins.mnemonic:<8s} {ins.op_str}")

# find the function that contains 0x5F3CA by scanning back for CC padding
for anchor in (0x5F3CA, 0x5E913, 0x67E67, 0x68203, 0x68C52, 0x68F21, 0x76FC3):
    start = find_func_start(anchor)
    print(f"anchor 0x{anchor:X} -> func start 0x{start:X}")

start = find_func_start(0x5F3CA)
disasm_linear(start, 0x700, "font.lmp loader (from func start)")