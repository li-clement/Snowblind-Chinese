#!/usr/bin/env python3
# xbe_fontrefs.py - find code references to font-related strings and disassemble around them
import struct, sys, os

from capstone import Cs, CS_ARCH_X86, CS_MODE_32

XBE = r"E:\Game\ps5\iso\[XBOX].Baldur's.Gate.Dark.Alliance.[USA]\default.xbe"
TEXT_VA = 0x11000
TEXT_RAW = 0x1000
TEXT_SIZE = 0xDC79C

print("capstone import worked" , )
try:
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = False
    print("disasm engine ok")
except Exception as e:
    print("disasm unavailable:", e)
    sys.exit(1)

b = open(XBE, 'rb').read()
text = b[TEXT_RAW:TEXT_RAW + TEXT_SIZE]

targets = {
    'font.lmp': 0x13D7F8,
    'gamefonta.fnt': 0x13D7E8,
    'gamefontmed.fnt': 0x13D7D8,
    'gamefontsmall.fnt': 0x13D7C4,
    'frontend.lmp': 0x13EDEC,
    'bigfont.fnt': 0x13EFB0,
    'creditfont.fnt': 0x13EF80,
    'gtext.lmp': 0x13D7B8,
    'hud.lmp': 0x13D70C,
    'mapicons.lmp': 0x13D6FC,
    'mouth.lmp': 0x13D6F0,
    'loading.lmp': 0x13D6D4,
    'config.lmp': 0x13EECC,
    'mainmenu.lmp': 0x13D72C,
    'menu_subtitles': 0x13DA38,
    'menu_showdialog': 0x13DA48,
    'dialog.bin': 0x146CE0,
}

print("== xref scan (.text) ==")
xrefs = {}   # va -> list of target names
for off in range(0, len(text) - 3):
    v = struct.unpack_from('<I', text, off)[0]
    for name, va in targets.items():
        if v == va:
            xrefs.setdefault(TEXT_VA + off, []).append(name)
# also 16-bit partial? no.
for va in sorted(xrefs):
    print(f"  0x{va:X} ({va - TEXT_VA + TEXT_RAW:#x} file): {', '.join(xrefs[va])}")

# disassemble around each xref
def disasm_region(va, n=40):
    off = TEXT_RAW + (va - TEXT_VA)
    start = max(0, off - 32)
    end = min(len(text), off + n * 6)
    print(f"--- disasm near 0x{va:X} ---")
    for ins in md.disasm(text[start:end], TEXT_VA + (start - TEXT_RAW)):
        mark = ' >>>' if (TEXT_VA + (start - TEXT_RAW) + ins.address - (TEXT_VA + start - TEXT_RAW)) in (0,) else ''
        print(f"  0x{ins.address:06X}: {ins.mnemonic}\t{ins.op_str}")

# disassemble function that references font.lmp - find surrounding code
for va in sorted(xrefs):
    names = xrefs[va]
    if any(n in ('font.lmp', 'gamefonta.fnt', 'gamefontmed.fnt', 'gamefontsmall.fnt',
                 'bigfont.fnt', 'creditfont.fnt', 'frontend.lmp') for n in names):
        print("\n" + "=" * 70)
        print(f"xref at VA 0x{va:X} -> {names}")
        disasm_region(va, n=60)