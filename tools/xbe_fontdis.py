#!/usr/bin/env python3
# xbe_fontdis.py - disassemble the font loader function around 0x5F3CA
import struct
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

XBE = r"E:\Game\ps5\iso\[XBOX].Baldur's.Gate.Dark.Alliance.[USA]\default.xbe"
TEXT_VA, TEXT_RAW, TEXT_SIZE = 0x11000, 0x1000, 0xDC79C
b = open(XBE, 'rb').read()
text = b[TEXT_RAW:TEXT_RAW + TEXT_SIZE]

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True

def disasm(start_va, nbytes, label=""):
    off = TEXT_RAW + (start_va - TEXT_VA)
    print(f"\n===== {label} @0x{start_va:X} =====")
    code = text[off:off + nbytes]
    for ins in md.disasm(code, start_va):
        print(f"  0x{ins.address:06X}: {ins.mnemonic:<8s} {ins.op_str}")

# The font.lmp loader xrefs at 0x5F3CA..0x5F41D. Find function start: scan backwards for prologue
def find_func_start(va):
    off = TEXT_RAW + (va - TEXT_VA)
    # look back up to 0x400 bytes for int3 padding / push ebp / sub esp
    s = max(0, off - 0x400)
    window = text[s:off]
    # find last byte sequence that looks like a function prologue
    best = None
    i = len(window) - 1
    while i > 0:
        if window[i] == 0xC3 and i + 1 < len(window) and window[i+1] == 0x90:  # ret; nop
            best = i + 1
            break
        i -= 1
    if best is None:
        best = 0
    return TEXT_VA + (s + best)

for anchor in (0x5F3CA, 0x68203, 0x67E67, 0x68C52, 0x68F21):
    start = find_func_start(anchor)
    print(f"anchor 0x{anchor:X} -> func start ~0x{start:X}")
    if 0x5F000 <= start <= 0x61000:
        disasm(start, 0x650, "font.lmp loader")
    elif 0x67000 <= start <= 0x69500:
        disasm(start, 0x400, "frontend loader")
    else:
        disasm(start, 0x200, "other")