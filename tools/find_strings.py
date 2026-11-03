import re
b = open(r"E:\Game\ps5\iso\[XBOX].Baldur's.Gate.Dark.Alliance.[USA]\default.xbe", 'rb').read()
print('total size', len(b))
for s in [b'japfontbig0', b'gamefonta', b'gamefontmed', b'gamefontsmall', b'bigfont', b'creditfont', b'font.lmp', b'frontend.lmp', b'.fnt']:
    hits = [m.start() for m in re.finditer(re.escape(s), b)]
    print(f'{s.decode()}: {len(hits)} refs, first at {[hex(h) for h in hits[:4]]}')