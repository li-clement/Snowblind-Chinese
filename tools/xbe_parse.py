#!/usr/bin/env python3
# xbe_parse.py - parse XBE properly, list sections, locate strings and code refs
import struct, sys, re, os

XBE_SECTION = struct.Struct('<IIIIIIIIII20s')  # 10 dwords + 20-byte digest = 60 bytes
# NOTE: real XBE_SECTION_HEADER is 56 bytes (10 fields incl 20B digest); verify during parse

def va_to_file(sections, va, base=0x10000):
    """map runtime VA to file offset using section table; return (offset, section) or None"""
    for s in sections:
        vaddr, vsize, rawaddr, rawsize = s['vaddr'], s['vsize'], s['rawaddr'], s['rawsize']
        if vaddr <= va < vaddr + vsize:
            return rawaddr + (va - vaddr), s
    # try base-relative (before any section, e.g. header region)
    return None

def parse(path):
    b = open(path, 'rb').read()
    assert b[0:4] == b'XBEH'
    base, hdrsz, imgsz, img_hdr_sz, td = struct.unpack_from('<IIIII', b, 0x104)
    cert, nsect, sectdir, initflags, entry = struct.unpack_from('<IIIII', b, 0x118)
    tls, stack, heap_res, heap_commit, pebase = struct.unpack_from('<IIIII', b, 0x12C)
    print(f"base=0x{base:X} hdrsz=0x{hdrsz:X} imgsz=0x{imgsz:X} imgHdrSz=0x{img_hdr_sz:X} timedate=0x{td:08X} ({td} = {__import__('datetime').datetime.utcfromtimestamp(td)})")
    print(f"cert=0x{cert:X} nsect={nsect} sectdir=0x{sectdir:X} initflags=0x{initflags:X} entry_raw=0x{entry:08X}")
    print(f"tls=0x{tls:X} stack=0x{stack:X} heapRes=0x{heap_res:X} heapCommit=0x{heap_commit:X} pebase=0x{pebase:X}")
    # entry decode
    for name, key in (('debug', 0x94859D4B), ('retail', 0xA8FC57AB)):
        e = entry ^ key
        if e < imgsz + base:
            print(f"  entry (XOR {name}): 0x{e:X}")
    # sections: sectdir VA -> file offset (usually 0x36C)
    foff = sectdir - base
    sections = []
    for i in range(nsect):
        p = foff + i * 56
        flags, vaddr, vsize, rawaddr, rawsize, nameva, namecnt, headpg, tailpg, = struct.unpack_from('<IIIIIIIII', b, p)
        digest = b[p + 36:p + 56]
        # name: VA -> file
        nf = nameva - base
        nm = ''
        if 0 <= nf < len(b):
            nm = b[nf:b.find(b'\x00', nf)].decode('ascii', 'replace')
        sections.append(dict(flags=flags, vaddr=vaddr, vsize=vsize, rawaddr=rawaddr,
                             rawsize=rawsize, nameva=nameva, name=nm, digest=digest))
        print(f"  S{i}: name={nm!r} flags=0x{flags:08X} VA=0x{vaddr:X} VS=0x{vsize:X} "
              f"raw=0x{rawaddr:X} rawSize=0x{rawsize:X} ratio={rawsize/vsize if vsize else 1:.3f}")
    # certificate info
    cf = cert - base
    titleid, = struct.unpack_from('<I', b, cf + 0x04)
    print(f"cert titleID=0x{titleid:08X}")
    # print all strings in .rdata / last sections
    for s in sections:
        if 'rdata' in s['name'] or 'data' in s['name']:
            raw = b[s['rawaddr']:s['rawaddr'] + s['rawsize']]
            interesting = []
            for m in re.finditer(rb'[\x20-\x7e]{5,}', raw):
                t = m.group(0).decode('latin1')
                if any(k in t.lower() for k in ('font', 'lmp', 'glyph', 'menu', 'dialog', 'text', 'subtitle', 'lang', 'uni', 'load')):
                    interesting.append((s['rawaddr'] + m.start(), t[:100]))
            print(f"\n== {s['name']} font-related strings ({len(interesting)}) ==")
            seen = set()
            for off, t in interesting:
                if t not in seen:
                    seen.add(t)
                    print(f"  file 0x{off:X} VA 0x{off + base:X}: {t}")
    return b, sections, base

if __name__ == '__main__':
    p = sys.argv[1]
    b, sections, base = parse(p)
    # dump text section raw for later analysis
    for s in sections:
        if s['name'] == '.text':
            out = os.path.join(os.path.dirname(p), '_xbe_text_raw.bin') if os.path.dirname(p) else '_xbe_text_raw.bin'
            with open(out, 'wb') as f:
                f.write(b[s['rawaddr']:s['rawaddr'] + s['rawsize']])
            print(f"\nwrote .text ({s['rawsize']} bytes) -> {out}")