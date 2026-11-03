import struct
XBE = r"E:\Game\ps5\iso\[XBOX].Baldur's.Gate.Dark.Alliance.[USA]\default.xbe"
TEXT_VA, TEXT_RAW, TEXT_SIZE = 0x11000, 0x1000, 0xDC79C
b = open(XBE, 'rb').read()
text = b[TEXT_RAW:TEXT_RAW + TEXT_SIZE]

def hexdump(va, n=0x100):
    o = TEXT_RAW + (va - TEXT_VA)
    for i in range(0, n, 16):
        chunk = b[o + i:o + i + 16]
        print('%06X: %s' % (va + i, ' '.join('%02X' % x for x in chunk)))

if __name__ == '__main__':
    import sys
    cmd = sys.argv[1]
    if cmd == 'hex':
        va = int(sys.argv[2], 16)
        n = int(sys.argv[3], 16) if len(sys.argv) > 3 else 0x100
        hexdump(va, n)
    elif cmd == 'dword':
        # scan for dword imm == target, disambiguate code vs data by context flag
        tgt = int(sys.argv[2], 16)
        imm = struct.pack('<I', tgt)
        pos = 0
        hits = []
        while True:
            i = text.find(imm, pos)
            if i < 0:
                break
            hits.append(TEXT_VA + i)
            pos = i + 1
        print('dword 0x%08X found at %d places' % (tgt, len(hits)))
        for h in hits:
            print('  0x%06X' % h)
    elif cmd == 'byte':
        # find byte pattern
        pat = bytes(int(x, 16) for x in sys.argv[2].split(','))
        pos = 0
        cnt = 0
        while True:
            i = text.find(pat, pos)
            if i < 0:
                break
            print('  0x%06X' % (TEXT_VA + i))
            cnt += 1
            pos = i + 1
        print('total %d hits' % cnt)