#!/usr/bin/env python3
# restore_res.py - copy all backup_original files back into res (clean slate)
import os, shutil, sys

BASE = r'E:\Game\ps5\iso'
RES  = os.path.join(BASE, "[XBOX].Baldur's.Gate.Dark.Alliance.[USA]", 'res')
BK   = os.path.join(BASE, 'backup_original')

n = 0
for f in os.listdir(BK):
    src = os.path.join(BK, f)
    dst = os.path.join(RES, f)
    shutil.copy2(src, dst)
    n += 1
print(f"restored {n} files to res")