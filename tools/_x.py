#!/usr/bin/env python3
# _x.py - CORRECT mapping: file = 0x1000 + (VA - 0x11000) for .text
# usage: python _x.py scan | python _x.py dis <va> <len>
import struct, sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

XBE = r"E:\Game\ps5\iso\[XBOX].Baldur's.Gate.Dark.Alliance.[USA]\default.xbe"
TEXT_VA, TEXT_RAW, TEXT_SIZE = 0x11000, 0x1000, 0xDC79C
b = open(XBE, 'rb').read()
text = b[TEXT_RAW:TEXT_RAW + TEXT_SIZE]      # text[0] <-> VA TEXT_VA ; file = TEXT_RAW + (VA - TEXT_VA)
md = Cs(CS_ARCH_X86, CS_MODE_32)

STR = {0x13ED98:'font.lmp',0x13ED88:'gamefonta.fnt',0x13ED78:'gamefontmed.fnt',0x13ED64:'gamefontsmall.fnt',0x13ED58:'gtext.lmp',0x14038C:'frontend.lmp',0x140520:'creditfont.fnt',0x140550:'bigfont.fnt',0x13EC90:'str13ec90'}

if sys.argv[1] == 'scan':
    pats = {
        b'\xA1\x44\x3F\x23\x00': 'mov eax,[0x233F44]',
        b'\xA1\x48\x3F\x23\x00': 'mov eax,[0x233F48]',
        b'\xA1\x4C\x3F\x23\x00': 'mov eax,[0x233F4C]',
        b'\xA1\x0C\x3F\x23\x00': 'mov eax,[0x233F0C]',
    }
    for pat, nm in pats.items():
        pos = 0
        while True:
            i = text.find(pat, pos)
            if i < 0: break
            print(f"0x{TEXT_VA+i:06X} (file 0x{TEXT_RAW+i:X}) {nm}")
            pos = i + 1
elif sys.argv[1] == 'dword':
    # find all dword == given va
    target = int(sys.argv[2], 16)
    for off in range(0, len(text)-3):
        v = struct.unpack_from('<I', text, off)[0]
        if v == target:
            print(f"0x{TEXT_VA+off:06X} (file 0x{TEXT_RAW+off:X})")
elif sys.argv[1] == 'dis':
    start = int(sys.argv[2], 16)
    n = int(sys.argv[3], 16)
    off = start - TEXT_VA
    code = text[off:off+n]
    print(f"===== dis 0x{start:X} (file 0x{TEXT_RAW+off:X}, len {n:#x}) =====")
    for ins in md.disasm(code, start):
        op = ins.op_str
        extra = ''
        if ins.mnemonic in ('call','jmp','je','jne','jg','jl','jge','jle','ja','jb','jae','jbe','js','jns','jz','jnz','loop','loope','loopne'):
            try:
                t = int(op,16)
                extra = f"  ; ->0x{t:X}"
                if 0x115380 <= t < 0x115380+0x11B60: extra += f" [D3Dsec]"
            except: pass
        elif ins.mnemonic in ('push','mov'):
            try:
                v = int(op.split()[-1],16)
                if v in STR: extra = f"  ; <{STR[v]}>"
            except: pass
        print(f"  0x{ins.address:06X}: {ins.mnemonic:<8s} {op}{extra}")
elif sys.argv[1] == 'hex':
    start = int(sys.argv[2], 16)
    n = int(sys.argv[3], 16) if len(sys.argv) > 3 else 0x40
    off = start - TEXT_VA
    data = text[off:off+n]
    for i in range(0, len(data), 16):
        chunk = data[i:i+16]
        hexs = ' '.join(f'{x:02X}' for x in chunk)
        asc = ''.join(chr(x) if 32<=x<127 else '.' for x in chunk)
        print(f"  0x{start+i:06X}: {hexs:<48s} {asc}")