#!/usr/bin/env python3
# _dis2.py - CORRECTED disassembler: text index = VA - TEXT_VA; file = TEXT_RAW + (VA - TEXT_VA)
# usage: python _dis2.py <va> <len> [annotate]
import sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

XBE = r"E:\Game\ps5\iso\[XBOX].Baldur's.Gate.Dark.Alliance.[USA]\default.xbe"
TEXT_VA, TEXT_RAW, TEXT_SIZE = 0x11000, 0x1000, 0xDC79C
b = open(XBE, 'rb').read()
text = b[TEXT_RAW:TEXT_RAW + TEXT_SIZE]
md = Cs(CS_ARCH_X86, CS_MODE_32)

STR = {0x13ED98: 'font.lmp', 0x13ED88: 'gamefonta.fnt', 0x13ED78: 'gamefontmed.fnt',
       0x13ED64: 'gamefontsmall.fnt', 0x13ED58: 'gtext.lmp', 0x14038C: 'frontend.lmp',
       0x140520: 'creditfont.fnt', 0x140550: 'bigfont.fnt', 0x13EC90: 'str_13ec90',
       0x138958: 'str_138958(gtextcontainer?)', 0x13EDA4: 'str_13eda4',
       0x13ED4C: 'str_13ed4c', 0x13ED40: 'str_13ed40', 0x13ED34: 'str_13ed34',
       0x13ED24: 'str_13ed24', 0x13ED18: 'str_13ed18', 0x13ED0C: 'str_13ed0c',
       0x13ED00: 'str_13ed00', 0x13ECC0: 'str_13ecc0'}

start = int(sys.argv[1], 16)
n = int(sys.argv[2], 16)
off = start - TEXT_VA
code = text[off:off + n]
print("===== dis 0x%X (file 0x%X, len 0x%X) =====" % (start, TEXT_RAW + off, n))
for ins in md.disasm(code, start):
    op = ins.op_str
    extra = ''
    if ins.mnemonic in ('call', 'jmp', 'je', 'jne', 'jg', 'jl', 'jge', 'jle', 'ja', 'jb', 'jae', 'jbe', 'js', 'jns', 'jz', 'jnz'):
        try:
            t = int(op, 16)
            extra = '  ; ->0x%X' % t
            if 0x114000 <= t < 0x118000:
                extra += ' [D3D]'
            if t in (0x7EFB0, 0x7F000):
                extra += ' <LMPLOAD>'
        except:
            pass
    elif ins.mnemonic in ('push', 'mov'):
        parts = op.split()
        if parts:
            try:
                v = int(parts[-1], 16)
                if v in STR:
                    extra = '  ; <%s>' % STR[v]
                elif v in (0x233F44, 0x233F48, 0x233F4C):
                    extra = '  ; <fontslot %X>' % v
            except:
                pass
    print('  0x%06X: %-8s %s%s' % (ins.address, ins.mnemonic, op, extra))