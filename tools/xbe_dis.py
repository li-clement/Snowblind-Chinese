#!/usr/bin/env python3
# xbe_fontdis3.py - disassemble specific range
import sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

XBE = r"E:\Game\ps5\iso\[XBOX].Baldur's.Gate.Dark.Alliance.[USA]\default.xbe"
TEXT_VA, TEXT_RAW, TEXT_SIZE = 0x11000, 0x1000, 0xDC79C
b = open(XBE, 'rb').read()
text = b[TEXT_RAW:TEXT_RAW + TEXT_SIZE]
md = Cs(CS_ARCH_X86, CS_MODE_32)

start = int(sys.argv[1], 16)
n = int(sys.argv[2], 16)
off = start - TEXT_VA  # offset inside text slice
code = text[off:off + n]
for ins in md.disasm(code, start):
    print(f'  0x{ins.address:06X}: {ins.mnemonic:<9s} {ins.op_str}')