#!/usr/bin/env python3
# xbe_fontload2.py - fixed offsets: byte i in text slice <-> VA TEXT_VA+i
import struct, sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

XBE = r"E:\Game\ps5\iso\[XBOX].Baldur's.Gate.Dark.Alliance.[USA]\default.xbe"
TEXT_VA, TEXT_RAW, TEXT_SIZE = 0x11000, 0x1000, 0xDC79C
b = open(XBE, 'rb').read()
text = b[TEXT_RAW:TEXT_RAW + TEXT_SIZE]
md = Cs(CS_ARCH_X86, CS_MODE_32)

font_strings = {
    0x13ED98: 'font.lmp', 0x13ED88: 'gamefonta.fnt', 0x13ED78: 'gamefontmed.fnt',
    0x13ED64: 'gamefontsmall.fnt', 0x13ED58: 'gtext.lmp',
    0x14038C: 'frontend.lmp', 0x140520: 'creditfont.fnt', 0x140550: 'bigfont.fnt',
}

print("== push imm32 / mov reg,imm32 (fixed) ==")
hits = []
for va, nm in font_strings.items():
    imm = struct.pack('<I', va)
    for prefix in (b'\x68', b'\xB8', b'\xB9', b'\xBA', b'\xBB', b'\xBC', b'\xBD', b'\xBE', b'\xBF'):
        pat = prefix + imm
        pos = 0
        while True:
            i = text.find(pat, pos)
            if i < 0: break
            hits.append((TEXT_VA + i, nm, prefix))
            pos = i + 1

def func_start_idx(i):
    s = i
    while s > 0 and s > i - 0x4000:
        if text[s] == 0xCC:
            s -= 1
            continue
        if s + 1 < len(text) and text[s + 1] == 0xCC and text[s] != 0xCC:
            return s + 1
        s -= 1
    return 0

print(f"{'VA':>8s} {'name':<18s} {'func start':>10s}")
seen = {}
for va, nm, pref in sorted(hits):
    i = va - TEXT_VA
    fs = func_start_idx(i)
    seen.setdefault(fs, []).append((va, nm))
    print(f"0x{va:06X} {nm:<18s} 0x{fs + TEXT_VA:06X}")

# disassemble the font.lmp loader function (0x5F005-ish) properly from true start idx
fs = min(k for k in seen if any('font.lmp' in n or 'gamefonta' in n for _, n in seen[k]))
start_va = fs + TEXT_VA
print(f"\n===== disasm font loader @0x{start_va:X} (len 0x800) =====")
code = text[fs:fs + 0x800]
for ins in md.disasm(code, start_va):
    if ins.address > 0x5F800:  # only print until font load section
        pass
    print(f"  0x{ins.address:06X}: {ins.mnemonic:<9s} {ins.op_str}")