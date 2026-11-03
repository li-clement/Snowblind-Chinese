#!/usr/bin/env python3
# xbe_fontload.py - byte-pattern search for push/mov imm32 of font string VAs,
# then disassemble the containing function
import struct, sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

XBE = r"E:\Game\ps5\iso\[XBOX].Baldur's.Gate.Dark.Alliance.[USA]\default.xbe"
TEXT_VA, TEXT_RAW, TEXT_SIZE = 0x11000, 0x1000, 0xDC79C
b = open(XBE, 'rb').read()
text = b[TEXT_RAW:TEXT_RAW + TEXT_SIZE]

font_strings = {
    0x13ED98: 'font.lmp', 0x13ED88: 'gamefonta.fnt', 0x13ED78: 'gamefontmed.fnt',
    0x13ED64: 'gamefontsmall.fnt', 0x13ED58: 'gtext.lmp',
    0x14038C: 'frontend.lmp', 0x140520: 'creditfont.fnt', 0x140550: 'bigfont.fnt',
    0x14055C: 'frontendmenu.tex', 0x140570: 'frontendmenulong.tex',
}

print("== push imm32 / mov reg,imm32 of font string VAs ==")
hits = []
for va, nm in font_strings.items():
    imm = struct.pack('<I', va)
    # push imm32 = 68 xx xx xx xx
    pat = b'\x68' + imm
    pos = 0
    while True:
        i = text.find(pat, pos)
        if i < 0: break
        hits.append((TEXT_VA + i, 'push', nm))
        pos = i + 1
    # mov reg, imm32: B8-BF xx xx xx xx
    for regop in range(0xB8, 0xC0):
        pat = bytes([regop]) + imm
        pos = 0
        while True:
            i = text.find(pat, pos)
            if i < 0: break
            hits.append((TEXT_VA + i, 'mov r%d' % (regop - 0xB8), nm))
            pos = i + 1

md = Cs(CS_ARCH_X86, CS_MODE_32)
for va, kind, nm in sorted(hits):
    off = TEXT_RAW + (va - TEXT_VA)
    ins = next(md.disasm(text[off:off + 8], va))
    print(f"  0x{va:06X}: {kind} {nm:18s}  [{ins.mnemonic} {ins.op_str}]")

# find function boundaries for hits (int3 padding backwards)
def func_start(va):
    off = TEXT_RAW + (va - TEXT_VA)
    s = off
    while s > 0x1000 and s > off - 0x2000:
        if text[s] == 0xCC:
            s -= 1
            continue
        if s + 1 < len(text) and text[s + 1] == 0xCC:
            return TEXT_VA + (s - TEXT_RAW) + 1
        if text[s] == 0x90 and text[s - 1] == 0x90:
            t = s
            while t > 0 and text[t] == 0x90:
                t -= 1
            return TEXT_VA + (t + 1 - TEXT_RAW)
        s -= 1
    return None

print("\n== functions containing these hits ==")
for va, kind, nm in sorted(hits):
    fs = func_start(va)
    print(f"  0x{va:06X} {nm} -> func start 0x{fs:X}" if fs else f"  0x{va:06X} {nm} -> ?")