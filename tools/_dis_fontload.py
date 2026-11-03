from capstone import Cs, CS_ARCH_X86, CS_MODE_32
XBE = r"E:\Game\ps5\iso\[XBOX].Baldur's.Gate.Dark.Alliance.[USA]\default.xbe"
b = open(XBE,'rb').read()
TEXT_VA, TEXT_RAW, TEXT_SIZE = 0x11000, 0x1000, 0xDC79C
text = b[TEXT_RAW:TEXT_RAW+TEXT_SIZE]
md = Cs(CS_ARCH_X86, CS_MODE_32)
STR = {0x13ED98:'font.lmp',0x13ED88:'gamefonta.fnt',0x13ED78:'gamefontmed.fnt',0x13ED64:'gamefontsmall.fnt',0x13ED58:'gtext.lmp',0x14038C:'frontend.lmp',0x140520:'creditfont.fnt',0x140550:'bigfont.fnt',0x13EC90:'str13ec90',0x13ED4C:'str13ed4c',0x13ED40:'str13ed40',0x13ED34:'str13ed34',0x13ED24:'str13ed24',0x13E018:'str13e018'}
def dis(start, n):
    off = TEXT_RAW + (start - TEXT_VA)
    code = text[off:off+n]
    print(f"===== 0x{start:X} (len {n:#x}) =====")
    for ins in md.disasm(code, start):
        op = ins.op_str
        extra = ''
        if ins.mnemonic in ('call','jmp','je','jne','jg','jl','jge','jle','ja','jb','jae','jbe','js','jns','jz','jnz'):
            try:
                t = int(op,16)
                extra = f"  ; ->0x{t:X}"
                if t >= 0x115380 and t < 0x115380+0x11B60: extra += " [D3D]"
            except: pass
        elif ins.mnemonic in ('push','mov'):
            try:
                v = int(op.split()[-1],16)
                if v in STR: extra = f"  ; <{STR[v]}>"
            except: pass
        print(f"  0x{ins.address:06X}: {ins.mnemonic:<7s} {op}{extra}")
dis(0x5F3C4, 0x150)
