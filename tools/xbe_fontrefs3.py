#!/usr/bin/env python3
# xbe_fontrefs3.py - corrected VA mapping + font loader xrefs
import struct, sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

XBE = r"E:\Game\ps5\iso\[XBOX].Baldur's.Gate.Dark.Alliance.[USA]\default.xbe"
b = open(XBE, 'rb').read()

# sections (from xbe_parse): name: (vaddr, vsize, rawaddr, rawsize)
SECS = {
    '.text':   (0x11000, 0xDC79C, 0x1000,   0xDC79C),
    'XMV':     (0xED7A0, 0x27BC4, 0xDE000,  0x27BB4),
    'D3D':     (0x115380, 0x11B60, 0x106000, 0xE704),
    'XGRPH':   (0x126EE0, 0xF98,   0x115000, 0xF94),
    'DSOUND':  (0x127E80, 0x8C04,  0x116000, 0x89C4),
    'XPP':     (0x130AA0, 0x7AF8,  0x11F000, 0x7AF8),
    '.rdata':  (0x1385A0, 0x18498, 0x127000, 0x18498),
    '.data':   (0x150A40, 0x3714BC,0x140000, 0x9B7C),
    'DOLBY':   (0x4C1F00, 0x7180,  0x14A000, 0x716C),
    '$$XTIMAGE':(0x4C9080,0x2800,  0x152000, 0x2800),
    '$$XSIMAGE':(0x4CB880,0x1000,  0x155000, 0x1000),
}

def file_to_va(fo):
    for nm, (vaddr, vsize, rawaddr, rawsize) in SECS.items():
        if rawaddr <= fo < rawaddr + rawsize:
            return vaddr + (fo - rawaddr), nm
    return None, None

def va_to_file(va):
    for nm, (vaddr, vsize, rawaddr, rawsize) in SECS.items():
        if vaddr <= va < vaddr + vsize:
            return rawaddr + (va - vaddr), nm
    return None, None

# font strings located by xbe_parse (file offsets given there)
font_strings = {
    0x12D7F8: 'font.lmp', 0x12D7E8: 'gamefonta.fnt', 0x12D7D8: 'gamefontmed.fnt',
    0x12D7C4: 'gamefontsmall.fnt', 0x12D7B8: 'gtext.lmp', 0x12D70C: 'hud.lmp',
    0x12D6FC: 'mapicons.lmp', 0x12D6F0: 'mouth.lmp', 0x12D6D4: 'loading.lmp',
    0x12EDEC: 'frontend.lmp', 0x12EF80: 'creditfont.fnt', 0x12EFB0: 'bigfont.fnt',
    0x12DA38: 'menu_subtitles', 0x12DA48: 'menu_showdialog',
    0x136CE0: 'dialog.bin', 0x13EFC0: '',  # placeholder
}
print("== corrected string VAs ==")
vas = {}
for fo, nm in sorted(font_strings.items()):
    va, sec = file_to_va(fo)
    if nm:
        vas[va] = nm
        print(f"  {nm:20s} file=0x{fo:X} VA=0x{va:X} ({sec})")

text_size = SECS['.text'][1]
text_raw = b[SECS['.text'][2]:SECS['.text'][2] + text_size]
print("\n== text refs to font string VAs ==")
for off in range(0, len(text_raw) - 3):
    v = struct.unpack_from('<I', text_raw, off)[0]
    if v in vas:
        print(f"  0x{SECS['.text'][0] + off:X}: ref 0x{v:X} -> {vas[v]}")

# also search .data / D3D / XPP sections
print("\n== refs in other sections ==")
for nm, (vaddr, vsize, rawaddr, rawsize) in SECS.items():
    if nm == '.text': continue
    sec = b[rawaddr:rawaddr + rawsize]
    for off in range(0, len(sec) - 3):
        v = struct.unpack_from('<I', sec, off)[0]
        if v in vas:
            print(f"  {nm} 0x{vaddr + off:X}: ref 0x{v:X} -> {vas[v]}")