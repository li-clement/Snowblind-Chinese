import sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

XBE = r"E:\Game\ps5\iso\[XBOX].Baldur's.Gate.Dark.Alliance.[USA]\default.xbe"
TEXT_VA, TEXT_RAW, TEXT_SIZE = 0x11000, 0x1000, 0xDC79C
b = open(XBE, 'rb').read()
text = b[TEXT_RAW:TEXT_RAW + TEXT_SIZE]
md = Cs(CS_ARCH_X86, CS_MODE_32)

targets = [int(a, 16) for a in sys.argv[1:]]
hits = {t: [] for t in targets}
for ins in md.disasm(text, TEXT_VA):
    for t in targets:
        ts = f'0x{t:x}'
        if ts in ins.op_str:
            hits[t].append(f'0x{ins.address:06X}: {ins.mnemonic} {ins.op_str}')

for t in targets:
    print(f'== refs to 0x{t:X} ==')
    for h in hits[t]:
        print('  ', h)