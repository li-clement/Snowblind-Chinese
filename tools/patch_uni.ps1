# patch_uni.ps1 (ASCII only) - full write-back pipeline:
#   zh JSON -> encode .uni (preserving original key order & duplicates) -> rebuild .lmp -> rebuild .gob
# Design: for each .uni file (EN base), parse original entries (ordered list w/ dup keys),
#   look up zh dict by key, build new .uni bytes with zh text, then rebuild containers.
$ErrorActionPreference = 'Stop'

$base = 'E:\Game\ps5\iso'
$res  = Join-Path $base '[XBOX].Baldur''s.Gate.Dark.Alliance.[USA]\res'
$tr   = Join-Path $base 'translation'
$backup = Join-Path $base 'backup_original'
New-Item -ItemType Directory -Force -Path $backup | Out-Null

# ---------- helpers ----------
function Parse-Uni([byte[]]$d){
    $items = New-Object System.Collections.Generic.List[object]
    $pos = 0; $len = $d.Length
    while($pos + 4 -lt $len){
        $kStart = $pos
        while($pos -lt $len -and $d[$pos] -ne 0){ $pos++ }
        if($pos -ge $len){ break }
        $key = [System.Text.Encoding]::ASCII.GetString($d[$kStart..($pos-1)])
        if($key -eq ''){ break }
        $pos++
        if($pos % 2 -ne 0){ $pos++ }
        $tStart = $pos
        while($pos + 1 -lt $len -and -not ($d[$pos] -eq 0 -and $d[$pos+1] -eq 0)){ $pos += 2 }
        $txt = ''
        if($pos - 1 -ge $tStart){ $txt = [System.Text.Encoding]::Unicode.GetString($d[$tStart..($pos-1)]) }
        $items.Add([PSCustomObject]@{ Key=$key; Text=$txt })
        $pos += 2
    }
    return $items
}

function Build-UniFromList($list){
    $ms = New-Object System.IO.MemoryStream
    $bw = New-Object System.IO.BinaryWriter($ms)
    foreach($it in $list){
        $keyBytes = [System.Text.Encoding]::ASCII.GetBytes($it.Key)
        $bw.Write($keyBytes)
        $bw.Write([byte]0)
        if(($keyBytes.Length % 2) -eq 0){ $bw.Write([byte]0) }
        $txtBytes = [System.Text.Encoding]::Unicode.GetBytes($it.Text)
        $bw.Write($txtBytes)
        $bw.Write([byte]0); $bw.Write([byte]0)
    }
    $bw.Flush()
    return $ms.ToArray()
}

function Read-ZhDict([string]$jsonPath){
    if(-not (Test-Path $jsonPath)){ return $null }
    $raw = Get-Content -LiteralPath $jsonPath -Raw -Encoding UTF8
    $obj = $raw | ConvertFrom-Json
    $ht = @{}
    foreach($p in $obj.PSObject.Properties){ $ht[$p.Name] = [string]$p.Value }
    return $ht
}

# ---------- load zh dicts ----------
$zhDicts = @{}   # uniFileName -> hashtable key->zh
foreach($jf in @('zh_act1.uni.json','zh_act2.uni.json','zh_act3.uni.json','zh_tavern.uni.json',
                 'zh_bthrone_cut.uni.json','zh_cuttown_cut.uni.json','zh_xantam.uni.json',
                 'zh_sewer1_cut.uni.json','zh_csewer1_cut.uni.json','zh_towert_cut.uni.json')){
    $p = Join-Path $tr $jf
    if(Test-Path $p){
        $dict = Read-ZhDict $p
        if($dict){
            $name = $jf -replace '^zh_','' -replace '\.json$',''
            $zhDicts[$name] = $dict
            Write-Output ("loaded {0}: {1} keys" -f $name, $dict.Count)
        }
    }
}
# gtext merged from parts
$g1 = Read-ZhDict (Join-Path $tr 'zh_gtext_part1.uni.json')
$g2 = Read-ZhDict (Join-Path $tr 'zh_gtext_part2.uni.json')
if($g1 -and $g2){
    $gm = @{}
    foreach($k in $g1.Keys){ $gm[$k] = $g1[$k] }
    foreach($k in $g2.Keys){ $gm[$k] = $g2[$k] }
    $zhDicts['gtext.uni'] = $gm
    Write-Output ("merged gtext.uni: {0} keys" -f $gm.Count)
}

Write-Output "`n== Stage 1: backup originals =="
$topLmps = Get-ChildItem -LiteralPath $res -File -Filter '*.lmp'
$gobs = Get-ChildItem -LiteralPath $res -Recurse -File -Filter '*.gob'
foreach($f in @($topLmps + $gobs)){
    $dst = Join-Path $backup $f.Name
    if(-not (Test-Path $dst)){ Copy-Item -LiteralPath $f.FullName -Destination $dst }
}
Write-Output ("backed up {0} files to {1}" -f ($topLmps.Count + $gobs.Count), $backup)

Write-Output "`n== Stage 2: rebuild gtext.lmp (standalone) =="
$gtextPath = Join-Path $res 'gtext.lmp'
$b = [System.IO.File]::ReadAllBytes($gtextPath)
$cnt = [BitConverter]::ToUInt32($b,0)
$gEntries = @()
$pos = 4
for($i=0;$i -lt $cnt;$i++){
    $nb = New-Object System.Collections.Generic.List[byte]
    for($k=0;$k -lt 56;$k++){ if($b[$pos+$k] -eq 0){ break }; [void]$nb.Add($b[$pos+$k]) }
    $nm = [System.Text.Encoding]::ASCII.GetString($nb.ToArray())
    $off = [BitConverter]::ToUInt32($b,$pos+56)
    $sz  = [BitConverter]::ToUInt32($b,$pos+60)
    $gEntries += [PSCustomObject]@{ Name=$nm; Off=$off; Size=$sz }
    $pos += 64
}
$newG = New-Object System.IO.MemoryStream
$bwG = New-Object System.IO.BinaryWriter($newG)
$bwG.Write($cnt)
foreach($e in $gEntries){
    $nb = New-Object byte[] 56
    $nb2 = [System.Text.Encoding]::ASCII.GetBytes($e.Name)
    [Array]::Copy($nb2, $nb, [Math]::Min($nb2.Length,56))
    $bwG.Write($nb)
    $bwG.Write([UInt32]0); $bwG.Write([UInt32]0)
}
$di = 0
foreach($e in $gEntries){
    $dataB = $null
    if($zhDicts.ContainsKey($e.Name) -and $e.Name -match '\.uni$'){
        $od = Parse-Uni (New-Object byte[] 0)  # placeholder
        # parse original content to preserve order
        $orig = New-Object byte[] $e.Size
        [Array]::Copy($b, $e.Off, $orig, 0, $e.Size)
        $items = Parse-Uni $orig
        $zh = $zhDicts[$e.Name]
        $newItems = New-Object System.Collections.Generic.List[object]
        $missing = 0
        foreach($it in $items){
            if($zh.ContainsKey($it.Key)){
                $newItems.Add([PSCustomObject]@{ Key=$it.Key; Text=$zh[$it.Key] })
            } else {
                $newItems.Add($it)   # keep original text if key not in dict
                $missing++
            }
        }
        $dataB = Build-UniFromList $newItems
        if($missing -gt 0){ Write-Output ("  WARN {0}: {1} keys not in zh dict (kept EN)" -f $e.Name, $missing) }
    } else {
        $dataB = New-Object byte[] $e.Size
        [Array]::Copy($b, $e.Off, $dataB, 0, $e.Size)
    }
    $offP = 4 + $di*64 + 56
    $cur = $newG.Position
    $bwG.Write($dataB)
    $newG.Position = $offP
    $bwG.Write([UInt32]$cur)
    $bwG.Write([UInt32]$dataB.Length)
    $newG.Position = $newG.Length
    $di++
}
$bwG.Flush()
[System.IO.File]::WriteAllBytes($gtextPath, $newG.ToArray())
Write-Output ("gtext.lmp rebuilt: {0}->{1} bytes" -f $b.Length, $newG.Length)

Write-Output "`n== Stage 3: rebuild .gob (inner lmps with uni) =="
foreach($gob in $gobs){
    $gb = [System.IO.File]::ReadAllBytes($gob.FullName)
    $gobEnts = @()
    $pos = 0
    while($pos + 40 -le $gb.Length){
        $nb = New-Object System.Collections.Generic.List[byte]
        for($k=0;$k -lt 32;$k++){ if($gb[$pos+$k] -eq 0){ break }; [void]$nb.Add($gb[$pos+$k]) }
        $nm = [System.Text.Encoding]::ASCII.GetString($nb.ToArray())
        if($nm -eq ''){ break }
        $off = [BitConverter]::ToUInt32($gb,$pos+32)
        $sz  = [BitConverter]::ToUInt32($gb,$pos+36)
        if($off + $sz -gt $gb.Length -or $sz -eq 0){ break }
        $gobEnts += [PSCustomObject]@{ Name=$nm; Off=$off; Size=$sz }
        $pos += 40
    }
    if($gobEnts.Count -eq 0){ continue }
    $changed = @()
    foreach($ge in $gobEnts){
        if($ge.Name -notmatch '\.lmp$'){ continue }
        $lmpRaw = New-Object byte[] $ge.Size
        [Array]::Copy($gb, $ge.Off, $lmpRaw, 0, $ge.Size)
        if($lmpRaw.Length -lt 4){ continue }
        $lc = [BitConverter]::ToUInt32($lmpRaw,0)
        if($lc -lt 1 -or $lc -gt 1000){ continue }
        # scan lmp entries for uni we have zh for
        $lpos = 4
        $lEnts = @()
        $hasZh = $false
        for($i=0;$i -lt $lc;$i++){
            $lb = New-Object System.Collections.Generic.List[byte]
            for($k=0;$k -lt 56;$k++){ if($lmpRaw[$lpos+$k] -eq 0){ break }; [void]$lb.Add($lmpRaw[$lpos+$k]) }
            $lnm = [System.Text.Encoding]::ASCII.GetString($lb.ToArray())
            $loff = [BitConverter]::ToUInt32($lmpRaw,$lpos+56)
            $lsz  = [BitConverter]::ToUInt32($lmpRaw,$lpos+60)
            $lEnts += [PSCustomObject]@{ Name=$lnm; Off=$loff; Size=$lsz }
            if($zhDicts.ContainsKey($lnm)){ $hasZh = $true }
            $lpos += 64
        }
        if(-not $hasZh){ continue }
        # rebuild this lmp
        $newL = New-Object System.IO.MemoryStream
        $bwL = New-Object System.IO.BinaryWriter($newL)
        $bwL.Write($lc)
        foreach($le in $lEnts){
            $nb = New-Object byte[] 56
            $nb2 = [System.Text.Encoding]::ASCII.GetBytes($le.Name)
            [Array]::Copy($nb2, $nb, [Math]::Min($nb2.Length,56))
            $bwL.Write($nb)
            $bwL.Write([UInt32]0); $bwL.Write([UInt32]0)
        }
        $di2 = 0
        foreach($le in $lEnts){
            $dataB = $null
            if($zhDicts.ContainsKey($le.Name) -and $le.Name -match '\.uni$'){
                $orig = New-Object byte[] $le.Size
                [Array]::Copy($lmpRaw, $le.Off, $orig, 0, $le.Size)
                $items = Parse-Uni $orig
                $zh = $zhDicts[$le.Name]
                $newItems = New-Object System.Collections.Generic.List[object]
                foreach($it in $items){
                    if($zh.ContainsKey($it.Key)){
                        $newItems.Add([PSCustomObject]@{ Key=$it.Key; Text=$zh[$it.Key] })
                    } else {
                        $newItems.Add($it)
                    }
                }
                $dataB = Build-UniFromList $newItems
            } else {
                $dataB = New-Object byte[] $le.Size
                [Array]::Copy($lmpRaw, $le.Off, $dataB, 0, $le.Size)
            }
            $offP = 4 + $di2*64 + 56
            $cur = $newL.Position
            $bwL.Write($dataB)
            $newL.Position = $offP
            $bwL.Write([UInt32]$cur)
            $bwL.Write([UInt32]$dataB.Length)
            $newL.Position = $newL.Length
            $di2++
        }
        $bwL.Flush()
        $changed += [PSCustomObject]@{ Name=$ge.Name; NewData=$newL.ToArray() }
    }
    if($changed.Count -eq 0){ continue }
    # rebuild gob
    $newGob = New-Object System.IO.MemoryStream
    $bwGo = New-Object System.IO.BinaryWriter($newGob)
    foreach($ge in $gobEnts){
        $nb = New-Object byte[] 32
        $nb2 = [System.Text.Encoding]::ASCII.GetBytes($ge.Name)
        [Array]::Copy($nb2, $nb, [Math]::Min($nb2.Length,32))
        $bwGo.Write($nb)
        $bwGo.Write([UInt32]0); $bwGo.Write([UInt32]0)
    }
    $di3 = 0
    foreach($ge in $gobEnts){
        $chg = $changed | Where-Object { $_.Name -eq $ge.Name } | Select-Object -First 1
        if($chg){ $dataB = $chg.NewData }
        else {
            $dataB = New-Object byte[] $ge.Size
            [Array]::Copy($gb, $ge.Off, $dataB, 0, $ge.Size)
        }
        $offP = $di3*40 + 32
        $cur = $newGob.Position
        $bwGo.Write($dataB)
        $newGob.Position = $offP
        $bwGo.Write([UInt32]$cur)
        $bwGo.Write([UInt32]$dataB.Length)
        $newGob.Position = $newGob.Length
        $di3++
    }
    $bwGo.Flush()
    [System.IO.File]::WriteAllBytes($gob.FullName, $newGob.ToArray())
    Write-Output ("  rebuilt {0}: {1} changed lmps, size {2}->{3}" -f $gob.Name, $changed.Count, $gb.Length, $newGob.Length)
}
Write-Output "`nDONE"