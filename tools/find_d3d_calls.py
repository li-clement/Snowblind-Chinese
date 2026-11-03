import struct
b = open(r"E:\Game\ps5\iso\[XBOX].Baldur's.Gate.Dark.Alliance.[USA]\default.xbe", 'rb').read()
TEXT_RAW, TEXT_VA, TEXT_SIZE = 0x1000, 0x11000, 0xDC79C
text = b[TEXT_RAW:TEXT_RAW+TEXT_SIZE]
def find_call_target(target):
    hits=[]
    for i in range(len(text)-5):
        if text[i]==0xE8:
            rel=struct.unpack_from('<i',text,i+1)[0]
            va=TEXT_VA+i
            if (va+5+rel)&0xffffffff==target: hits.append(va)
    return hits
for tgt in (0x1159C0,0x115B70,0x115FF0,0x118950,0x118990,0x1189F0):
    print(f'call {tgt:#x}: {[hex(x) for x in find_call_target(tgt)]}')