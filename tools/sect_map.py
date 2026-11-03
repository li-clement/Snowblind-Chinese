import struct
p = r"E:\Game\ps5\iso\[XBOX].Baldur's.Gate.Dark.Alliance.[USA]\default.xbe"
b = open(p, 'rb').read()
base = struct.unpack_from('<I', b, 0x104)[0]
nsect = struct.unpack_from('<I', b, 0x11C)[0]
sectdir = struct.unpack_from('<I', b, 0x120)[0]
print(f'base=0x{base:X} nsect={nsect} sectdir=0x{sectdir:X} (file {sectdir-base:X})')
sects = []
for i in range(nsect):
    p0 = (sectdir - base) + i*40
    flags, vaddr, vsize, raw, rsize, nameoff, nref, hshared, tshared, digest = struct.unpack_from('<IIIIIIIIII', b, p0)
    sects.append((flags, vaddr, vsize, raw, rsize, nameoff))
    print(f'sect{i}: flags={flags:#010X} va=0x{vaddr:08X} vsize=0x{vsize:X} raw=0x{raw:X} rsize=0x{rsize:X} nameoff=0x{nameoff:X}')
    if nameoff:
        no = nameoff - base
        nm = b[no:no+64].split(b'\0',1)[0].decode('latin1', 'replace')
        print(f'   name: {nm!r}')

# find section containing VA 0x1159C0 and file offset of VA 0x66230, 0x7F050, 0x13ED88
for va_target in (0x1159C0, 0x115B70, 0x115FF0, 0x118950, 0x66230, 0x7F050, 0x13ED88):
    found = None
    for fl, va, vs, rw, rs, no in sects:
        if va <= va_target < va + max(vs, rs):
            found = (fl, va, vs, rw, rs)
            break
    if found:
        fl, va, vs, rw, rs = found
        print(f'VA {va_target:#x} -> sect flags={fl:#x} raw=0x{rw:X} fileoff=0x{rw + (va_target - va):X}')
    else:
        print(f'VA {va_target:#x} -> NOT in any section')