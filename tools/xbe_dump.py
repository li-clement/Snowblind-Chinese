#!/usr/bin/env python3
# xbe_dump.py - parse XBE header, sections; decompress .text if LZNT-compressed
# usage: python xbe_dump.py <default.xbe> [--dump-text out.bin]
import struct, sys, os

def lznt_decompress(src, outsz):
    """LZNT1 (Xbox's RTLDecompressBuffer uses LZNT1) decompression."""
    out = bytearray()
    pos = 0
    n = len(src)
    while pos < n and len(out) < outsz:
        flags = src[pos]
        pos += 1
        if flags == 0:
            # 8 literal bytes
            chunk = src[pos:pos + 8]
            pos += len(chunk)
            out.extend(chunk)
            continue
        for i in range(8):
            if len(out) >= outsz:
                break
            if pos >= n:
                break
            if flags & (1 << i):
                if pos + 2 > n:
                    break
                disp_hi, lbyte = src[pos], src[pos + 1]
                pos += 2
                disp = disp_hi | ((lbyte & 0xF0) << 4)
                length = (lbyte & 0x0F) + 3
                if disp == 0 or disp > len(out):
                    out.append(0)
                    continue
                for j in range(length):
                    if len(out) >= outsz:
                        break
                    out.append(out[-disp])
            else:
                if pos >= n:
                    break
                out.append(src[pos])
                pos += 1
    return bytes(out[:outsz])

def main():
    path = sys.argv[1]
    b = open(path, 'rb').read()
    magic, = struct.unpack_from('<I', b, 0)
    print(f"size={len(b)} magic=0x{magic:08X}")
    # Standard XBE header layout:
    # 0x00 magic 'XBEH'; 0x08 base; 0x0C headers size; 0x10 image size; 0x14 image base;
    # 0x1C certificate VA; 0x20 section count; 0x24 section headers VA
    base, hdrSz, imgSz, imgBase = struct.unpack_from('<IIII', b, 0x08)
    certAddr, sectCnt, sectAddr = struct.unpack_from('<III', b, 0x1C)
    print(f"base=0x{base:X} hdrSz=0x{hdrSz:X} imgSz=0x{imgSz:X} imgBase=0x{imgBase:X} certAddr=0x{certAddr:X} sectCnt={sectCnt} sectAddr=0x{sectAddr:X}")
    secs = []
    for i in range(sectCnt):
        p = sectAddr + i * 24
        if p + 24 > len(b):
            print(f"  !! section header {i} out of file (p=0x{p:X})")
            break
        name = b[p:p + 8].split(b'\x00', 1)[0].decode('ascii', 'replace')
        flags, vsz, vaddr, fsz, fptr, = struct.unpack_from('<IIIII', b, p + 8)
        secs.append((name, flags, vsz, vaddr, fsz, fptr))
        print(f"  {name:<8s} flags=0x{flags:08X} virtSz=0x{vsz:X} virtAddr=0x{vaddr:X} fileSz=0x{fsz:X} fileOff=0x{fptr:X}")
    # find text section
    for name, flags, vsz, vaddr, fsz, fptr in secs:
        if name in ('.text', 'text', '.rdata', 'rdata') and fsz:
            print(f"\n== {name}: fileOff=0x{fptr:X} fileSz=0x{fsz:X} virtSz=0x{vsz:X} flags=0x{flags:08X}")
            raw = b[fptr:fptr + fsz]
            if len(raw) < fsz:
                print("  warning: truncated section read")
            # check PE header presence (uncompressed text usually starts with 0x60-style prolog or data)
            if name in ('.text', 'text'):
                import collections
                hist = collections.Counter(raw[:max(512, fsz // 4)])
                print("  first 64 bytes:", raw[:64].hex(' '))
                # If compressed, flags bit 0x1000000? XBE section flag: 0x100 = preload? Compressed text flag = 0x4?
                # Actually: XBE section flags: 0x00000004 = compressed? (per xbedump: XBE_SECTION_FLAG_COMPRESSED = 0x4)
                is_compressed = (flags & 0x4) != 0
                print(f"  flags&4 (compressed?) = {is_compressed}")
                if is_compressed:
                    # Try LZNT decompress: output size = vsz
                    try:
                        dec = lznt_decompress(raw, vsz)
                        print(f"  LZNT decompressed: {len(dec)} bytes (virtSz={vsz})")
                        dst = sys.argv[3] if len(sys.argv) > 3 and sys.argv[2] == '--dump-text' else None
                        if dst:
                            open(dst, 'wb').write(dec)
                            print(f"  wrote {dst}")
                    except Exception as e:
                        print("  decompress failed:", e)
                else:
                    dec = raw
                    dst = sys.argv[3] if len(sys.argv) > 3 and sys.argv[2] == '--dump-text' else None
                    if dst:
                        open(dst, 'wb').write(dec)
                        print(f"  wrote {dst} ({len(dec)} bytes)")
    # also dump rdata for string xrefs
    for name, flags, vsz, vaddr, fsz, fptr in secs:
        if name in ('.rdata', 'rdata'):
            print(f"\n== {name}: fileOff=0x{fptr:X} fileSz=0x{fsz:X}")
            raw = b[fptr:fptr + fsz]
            # find interesting strings
            import re
            for m in re.finditer(rb'[ -~]{8,}', raw):
                s = m.group(0).decode('latin1')
                if any(k in s for k in ('font', 'Font', 'lmp', 'glyph', 'Glyph', 'CreateTexture', 'texture')):
                    print(f"  0x{m.start():X}: {s[:120]}")

if __name__ == '__main__':
    main()