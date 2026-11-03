import struct, os, subprocess, tempfile
ISO = r'E:\Game\ps5\iso\bgda_zh_font_v9.iso'
EX = r'E:\Game\ps5\iso\tools\artifacts\extract-xiso.exe'
TMP = tempfile.mkdtemp(prefix='v9chk_')
r = subprocess.run([EX, '-d', TMP, ISO, 'res/font.lmp', 'res/frontend.lmp'],
                   capture_output=True, text=True)
print('extract rc', r.returncode, r.stderr[-200:] if r.stderr else '')

def verify(path):
    b = open(path, 'rb').read()
    c = struct.unpack_from('<I', b, 0)[0]
    cur = 4 + c * 64
    cur = (cur + 0x7F) & ~0x7F
    ok = True
    for i in range(c):
        p = 4 + i * 64
        nm = b[p:p + 56].split(b'\x00', 1)[0].decode('latin1')
        off, sz = struct.unpack_from('<II', b, p + 56)
        if not (off == cur and off % 0x80 == 0 and off + sz <= len(b)):
            ok = False
        if '.fnt' in nm:
            fb = b[off:off + sz]
            cnt, hgt = struct.unpack_from('<HH', fb, 0)
            _, _, oSec, oBmp = struct.unpack_from('<IIII', fb, 4)
            atw, ath = struct.unpack_from('<HH', fb, oBmp)
            print(f'  {nm}: off=0x{off:X} sz={sz} cnt={cnt} hgt={hgt} atw={atw} ath={ath}')
        cur = (off + sz + 0x7F) & ~0x7F
    print(f'  layout ok: {ok}, total {len(b)}B')

verify(os.path.join(TMP, 'font.lmp'))
verify(os.path.join(TMP, 'frontend.lmp'))
print('tmp:', TMP)