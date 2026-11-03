#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v16 —— 复用 v14 已验证管线，做两件事：
   1) 中文字号在引擎硬约束内最大化。实测确认引擎对单个 .fnt 有 **256KB(0x40000)**
      载入上限（>0x40000 即字体加载失败→开局黑屏，已用 xemu 逐一实测钉死边界）。
      面积墙：全 1502 字 + 140 拉丁，em=12 时 1653*144+头部 > 0x40000 装不下；
      **em=11 是全字集的硬上限**，配合 0 间隙装箱可让全部 5 个字体都达标。
   2) 修标点：。！？一…… 按日版 japfontbig0 比例缩小墨迹并底对齐，不再撑满整格。

   安全：CJK/标点渲染进统一 px_h 高、底对齐的框，墨迹**严格落在 rect 内**；装箱 0 间隙
   依赖"引擎按 rect 半开区间 [x0,x1)×[y0,y1) 精确采样"——相邻格即使贴边也互不读入，
   故不串字（v13 串字是因为墨迹画到 rect 之外，这里用 stray==0 断言杜绝）。
"""
import struct, os
from PIL import Image, ImageDraw, ImageFont

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES  = os.path.join(BASE, "[XBOX].Baldur's.Gate.Dark.Alliance.[USA]", 'res')
BACK = os.path.join(BASE, 'backup_original')
ANA  = os.path.join(BASE, 'analysis')
JOBS = os.path.join(BASE, 'translation', 'jobs')

REC_START = 0x214
ALIGN     = 0x80
MAX_FNT   = 0x40000          # 引擎对单个 .fnt 的硬载入上限（实测）
ATW       = 1024
GUTTER    = 0                # 贴格装箱（靠墨迹裁入 rect 保证不串字）
MAX_H     = 228              # 1024 宽下使 .fnt<0x40000 的 ath 上限（实测 228 亮/230 黑）

TTF = '/System/Library/Fonts/Hiragino Sans GB.ttc'

# 标点墨迹高/宽比例（相对 em）——参考日版 japfontbig0 实测：。ink/cell≈0.33 ！/？≈0.79
PUNCT_H = {'。':0.34,'，':0.34,'、':0.32,'！':0.80,'？':0.80,'：':0.70,'；':0.70,
           '“':0.45,'”':0.45,'‘':0.45,'’':0.45,'（':0.90,'）':0.90,'…':0.34,
           '—':0.16,'《':0.60,'》':0.60,'「':0.50,'」':0.50,'·':0.22,'【':0.90,'】':0.90}
PUNCT_W = {'。':0.42,'，':0.42,'、':0.40,'！':0.40,'？':0.60,'：':0.40,'；':0.40,
           '“':0.50,'”':0.50,'（':0.60,'）':0.60,'…':0.95,'—':0.98,'《':0.60,'》':0.60,
           '「':0.50,'」':0.50,'·':0.34,'【':0.60,'】':0.60,'一':0.92}
# 横画类：宽度接近满格但高度很细
WIDE = {'一','—','…','＿','‾'}

def raster(ch, px_h, hfrac=1.0, wfrac=1.0):
    """等比栅格化，墨迹高≤round(px_h*hfrac)、宽≤round(px_h*wfrac)，返回 bool 行列。"""
    ih = max(1, round(px_h*hfrac)); iw = max(1, round(px_h*wfrac))
    big = max(px_h*8, 96)
    fnt = ImageFont.truetype(TTF, big)
    img = Image.new('L',(big*2,big*2),0)
    ImageDraw.Draw(img).text((big//2,big//2), ch, font=fnt, fill=255)
    bb = img.getbbox()
    if not bb: return None
    img = img.crop(bb); w,h = img.size
    sc = min(iw/w, ih/h)
    nw = max(1, round(w*sc)); nh = max(1, round(h*sc))
    img = img.resize((nw,nh), Image.LANCZOS); px = img.load()
    return [[1 if px[x,y]>96 else 0 for x in range(nw)] for y in range(nh)]

def load_font(b):
    cnt,hgt = struct.unpack_from('<HH', b, 0)
    nsect, magic, offSec, offBmp = struct.unpack_from('<IIII', b, 4)
    atw, ath = struct.unpack_from('<HH', b, offBmp)
    return dict(b=b, cnt=cnt, atw=atw, ath=ath, start=offBmp+1080,
                recs=[struct.unpack_from('<8H', b, REC_START+i*16) for i in range(cnt)],
                kerning=b[offSec:offBmp], magic=magic, nsect=nsect)

def latin_box(f, v, pad=1):
    """拉丁：原样像素 + 1px 自带留白（本就与原版无冲突）。返回 (rows, f5, adv, kern)。"""
    x0,x1,y0,y1 = v[1],v[2],v[3],v[4]; atw,ath,st = f['atw'],f['ath'],f['start']
    x0=max(0,x0-pad); y0=max(0,y0-pad); x1=min(x1+pad,atw); y1=min(y1+pad,ath)
    w=x1-x0; h=y1-y0
    if w<=0 or h<=0: return None
    rows=[[1 if f['b'][st+yy*atw+xx]>127 else 0 for xx in range(x0,x1)] for yy in range(y0,y1)]
    if not any(any(r) for r in rows): return None
    return (rows, v[5], v[6], v[7])

def crop_cols(rows):
    ys=[i for i,r in enumerate(rows) if any(r)]
    if not ys: return None
    xs=[j for i in range(ys[0],ys[-1]+1) for j,v in enumerate(rows[i]) if v]
    x0,x1=min(xs),max(xs)
    return [r[x0:x1+1] for r in rows[ys[0]:ys[-1]+1]]

def align_bottom(rows, px_h):
    """把任意墨迹放进 px_h 高的框，底对齐（基线在框底），列裁到墨迹宽度。"""
    cr = crop_cols(rows)
    if cr is None: return None
    h=len(cr)
    top=px_h-h
    canvas=[[0]*len(cr[0]) for _ in range(px_h)]
    for i,row in enumerate(cr):
        canvas[top+i]=row[:]
    # 顶行留空即可；确保墨迹严格在 [0,px_h) 内
    return canvas

def pack(entries, atw, gutter=GUTTER):
    """entries: list of (code, rows, f5, adv, kern)。0 间隙混高装箱。
       右侧预留 1 列（x+w>=atw 即换行），使任一格右边界 x1<=atw-1，避免引擎越界读。"""
    placed=[]; x=y=rh=0
    for code,rows,f5,adv,kern in entries:
        h=len(rows); w=max(len(r) for r in rows)
        if x+w>=atw: x=0; y+=rh+gutter; rh=0     # 留 1 列余量：右缘 x+w<=atw-1
        if h>rh: rh=h
        placed.append((code,x,y,w,h,f5,adv,kern,rows))
        x+=w+gutter
    ath=y+rh+ (gutter if placed else 0) + 1       # 底部再留 1 行，使 y1<=ath-1
    return placed, ath

def build_font(src_bytes, px_h, hanzi, punct, name):
    f = load_font(src_bytes)
    lat={v[0]:v for v in f['recs'] if v[0] not in (0,0xFFFF,32)}
    entries=[]
    # 拉丁先放（高一点，坐顶行），保留原 f5/adv/kern
    for c,v in lat.items():
        lb=latin_box(f,v)
        if lb: entries.append((c, lb[0], lb[1], lb[2], lb[3]))
    latk={c for c,_,_,_,_ in entries}
    # 汉字：统一 px_h 高、底对齐、满格宽（等比），保证基线整齐
    han=0
    for ch in hanzi:
        c=ord(ch)
        if c in latk or c in (0,0xFFFF,32): continue
        r=raster(ch, px_h, 0.92, 0.92)
        if not r: continue
        box=align_bottom(r, px_h)
        if not box: continue
        entries.append((c, box, 6, px_h, 0xFFFF)); han+=1
    # 标点：按日版比例缩小墨迹，底对齐；横画类保持细长
    pn=0
    for ch in punct:
        c=ord(ch)
        if c in latk or c in (0,0xFFFF,32): continue
        if ch in WIDE:
            r=raster(ch, px_h, PUNCT_H.get(ch,0.2), PUNCT_W.get(ch,0.95))
        else:
            r=raster(ch, px_h, PUNCT_H.get(ch,0.7), PUNCT_W.get(ch,0.6))
        if not r: continue
        box=align_bottom(r, px_h)
        if not box: continue
        entries.append((c, box, 6, px_h, 0xFFFF)); pn+=1
    placed, ath = pack(entries, ATW)
    # ---- 校验：尺寸、stray==0、rect 无重叠 ----
    atlas=bytearray(ATW*ath)
    rects=[]
    for code,x,y,w,h,f5,adv,kern,rows in placed:
        rects.append((x,y,x+w,y+h,code))
        for yy in range(h):
            for xx,vv in enumerate(rows[yy]):
                if vv: atlas[(y+yy)*ATW + x+xx]=255
    # overlap 检查（矩形两两，容许贴边；x 排序后早断）
    def overlap(a,b):
        return not (a[2]<=b[0] or b[2]<=a[0] or a[3]<=b[1] or b[3]<=a[1])
    overlaps=0
    R=sorted(rects)
    for i in range(len(R)):
        xi0,yi0,xi1,yi1,_=R[i]
        for j in range(i+1,len(R)):
            xj0,yj0,xj1,yj1,_=R[j]
            if xj0>=xi1: break
            if overlap((xi0,yi0,xi1,yi1),(xj0,yj0,xj1,yj1)): overlaps+=1
    cnt=len(placed)
    offSec=REC_START+cnt*16; offBmp=offSec+len(f['kerning']); start=offBmp+1080
    out=struct.pack('<HHIIII', cnt, 8, f['nsect'], f['magic'], offSec, offBmp)
    out+=f['b'][0x14:REC_START]                    # pre
    recs=bytearray()
    for code,x,y,w,h,f5,adv,kern,rows in placed:
        recs+=struct.pack('<8H', code, x, x+w, y, y+h, f5, adv, kern)
    out+=bytes(recs)+f['kerning']
    meta=f['b'][offBmp+4:offBmp+1080]
    out+=struct.pack('<HH', ATW, ath)+meta+bytes(atlas)
    size=len(out)
    eng_bm=offBmp+0x38+0x400; act_bm=len(out)-ATW*ath
    ok_sz = size<MAX_FNT; ok_bm = eng_bm==act_bm; ok_h = ath<=MAX_H
    flag = 'OK' if (ok_sz and ok_bm and ok_h and overlaps==0) else 'FAIL'
    print(f'{name:18s} glyphs={cnt} hanzi={han} punct={pn} ath={ath} size={size} '
          f'(0x40000={MAX_FNT}) bm={ok_bm} overlap={overlaps} [{flag}]')
    assert ok_sz, f'{name} size {size} >= 0x40000'
    assert ok_bm, f'{name} bm_match fail'
    assert ok_h,  f'{name} ath {ath}>{MAX_H}'
    assert overlaps==0, f'{name} {overlaps} rect overlaps'
    assert size == start+ATW*ath, f'{name} layout mismatch'
    return out

def parse_lmp(b):
    c=struct.unpack_from('<I',b,0)[0];out=[]
    for i in range(c):
        p=4+i*64; nm=b[p:p+56].split(b'\x00',1)[0].decode('latin1')
        off,size=struct.unpack_from('<II',b,p+56); out.append([nm,off,size])
    return out,c

def build_lmp(names, blobs):
    n=len(names); hdr_len=4+n*64; cur=hdr_len
    if cur%ALIGN: cur+=ALIGN-(cur%ALIGN)
    offs=[]
    for b in blobs:
        offs.append(cur); cur+=len(b)
        if cur%ALIGN: cur+=ALIGN-(cur%ALIGN)
    hdr=bytearray(struct.pack('<I',n))
    for i,nm in enumerate(names):
        hdr+=nm.encode('latin1')[:56].ljust(56,b'\x00')+struct.pack('<II',offs[i],len(blobs[i]))
    body=bytearray(); pos=hdr_len
    for i,b in enumerate(blobs):
        body+=b'\x00'*(offs[i]-pos); body+=b; pos=offs[i]+len(b)
    return bytes(hdr)+bytes(body)

def main():
    hanzi=open(os.path.join(JOBS,'zh_top1502.txt'),encoding='utf-8').read()
    punct=open(os.path.join(JOBS,'zh_punct.txt'),encoding='utf-8').read()
    print(f'hanzi={len(hanzi)} punct={len(punct)}  ATW={ATW} GUTTER={GUTTER} MAX_FNT=0x{MAX_FNT:X}')
    fontb=open(os.path.join(BACK,'font.lmp'),'rb').read()
    fe=open(os.path.join(BACK,'frontend.lmp'),'rb').read()
    def get(b,nm):
        for e,o,s in parse_lmp(b)[0]:
            if e==nm: return b[o:o+s]
    # 逐字体 px_h（可用 G16_PXH 统一覆盖，G16_GUTTER 覆盖间隙，用于隔离变量）
    P = int(os.environ.get('G16_PXH','11'))
    global GUTTER
    GUTTER = int(os.environ.get('G16_GUTTER', str(GUTTER)))
    spec_font  = {'gamefonta.fnt':P,'gamefontmed.fnt':P,'gamefontsmall.fnt':P}
    spec_fe    = {'bigfont.fnt':P,'creditfont.fnt':P,'gamefontsmall.fnt':P}
    built={}
    for nm,px in spec_font.items():
        built[nm]=build_font(get(fontb,nm), px, hanzi, punct, 'font/'+nm)
    for nm in spec_fe:
        key='fe/'+nm
        src=get(fe,nm)
        if src is None: continue
        if nm in built:      # gamefontsmall 复用同尺寸
            built['fe_'+nm]=built[nm] if spec_fe[nm]==spec_font.get(nm) else build_font(src,spec_fe[nm],hanzi,punct,key)
        else:
            built['fe_'+nm]=build_font(src, spec_fe[nm], hanzi, punct, key)
    # ---- 写回 font.lmp ----
    ents,_=parse_lmp(fontb); names=[e[0] for e in ents]; blobs=[]
    for nm,off,size in ents:
        blobs.append(built[nm] if nm in spec_font else fontb[off:off+size])
    new=build_lmp(names,blobs); open(os.path.join(RES,'font.lmp'),'wb').write(new)
    print(f'font.lmp {len(fontb)} -> {len(new)}')
    # ---- 写回 frontend.lmp ----
    fents,_=parse_lmp(fe); names=[e[0] for e in fents]; blobs=[]
    for nm,off,size in fents:
        if nm in spec_fe:
            blobs.append(built.get('fe_'+nm, built.get(nm)))
        else:
            blobs.append(fe[off:off+size])
    newfe=build_lmp(names,blobs); open(os.path.join(RES,'frontend.lmp'),'wb').write(newfe)
    print(f'frontend.lmp {len(fe)} -> {len(newfe)}')
    print('DONE v16')

if __name__=='__main__':
    main()
