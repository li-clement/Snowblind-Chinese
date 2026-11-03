# rebuild_uni.ps1 - Rebuild .uni binary from zh JSON, rebuild .lmp and .gob containers
# Usage: rebuild_uni.ps1 -Step encode|lmp|gob -JobDir <dir>
$ErrorActionPreference = 'Stop'
param(
    [Parameter(Mandatory=$true)][string]$Step,
    [string]$BaseDir = 'E:\Game\ps5\iso'
)

$res   = Join-Path $BaseDir '[XBOX].Baldur''s.Gate.Dark.Alliance.[USA]\res'
$trDir = Join-Path $BaseDir 'translation'
$work  = Join-Path $BaseDir 'work'
New-Item -ItemType Directory -Force -Path $work | Out-Null

# ---------- encode: zh JSON -> .uni binary (key \0 \0 + UTF16LE text \0) ----------
function Build-Uni([hashtable]$dict){
    $ms = New-Object System.IO.MemoryStream
    $bw = New-Object System.IO.BinaryWriter($ms)
    foreach($k in $dict.Keys){
        $keyBytes = [System.Text.Encoding]::ASCII.GetBytes($k)
        $bw.Write($keyBytes)      # key ASCII
        $bw.Write([byte]0)        # key terminator
        if(($keyBytes.Length % 2) -eq 0){ $bw.Write([byte]0) }  # pad to even text offset
        $txt = $dict[$k]
        $txtBytes = [System.Text.Encoding]::Unicode.GetBytes($txt)  # UTF-16LE
        $bw.Write($txtBytes)
        $bw.Write([byte]0); $bw.Write([byte]0)  # text terminator 00 00
    }
    $bw.Flush()
    return $ms.ToArray()
}

if($Step -eq 'encode'){
    $jobDir = Join-Path $trDir 'jobs'
    $files = Get-ChildItem -LiteralPath $jobDir -Filter 'en_*.uni.txt'
    $total = 0
    foreach($jf in $files){
        $fname = $jf.BaseName.Substring(3) + '.uni'   # en_act1.uni.txt -> act1.uni
        $zhPath = Join-Path $trDir ("zh_" + $fname + '.json')
        if(-not (Test-Path $zhPath)){ Write-Output "SKIP (no zh): $fname"; continue }
        $dict = Get-Content -LiteralPath $zhPath -Raw -Encoding UTF8 | ConvertFrom-Json
        # ConvertFrom-Json gives PSCustomObject; convert to hashtable
        $ht = @{}
        foreach($p in $dict.PSObject.Properties){ $ht[$p.Name] = [string]$p.Value }
        $bin = Build-Uni $ht
        $out = Join-Path $work ($fname + '.bin')
        [System.IO.File]::WriteAllBytes($out, $bin)
        Write-Output ("ENCODED {0}: {1} keys -> {2} bytes" -f $fname, $ht.Count, $bin.Length)
        $total += $ht.Count
    }
    Write-Output "TOTAL encoded: $total"
}
elseif($Step -eq 'lmp'){
    # Rebuild .lmp containers that contain .uni (gtext.lmp + each gob's inner lmp)
    # For gtext.lmp (standalone in res): replace entries directly
    $gtext = Join-Path $res 'gtext.lmp'
    $b = [System.IO.File]::ReadAllBytes($gtext)
    $count = [BitConverter]::ToUInt32($b,0)
    $entries = @()
    $pos = 4
    for($i=0;$i -lt $count;$i++){
        $nb = New-Object System.Collections.Generic.List[byte]
        for($k=0;$k -lt 56;$k++){ if($b[$pos+$k] -eq 0){ break }; [void]$nb.Add($b[$pos+$k]) }
        $nm = [System.Text.Encoding]::ASCII.GetString($nb.ToArray())
        $off = [BitConverter]::ToUInt32($b,$pos+56)
        $sz  = [BitConverter]::ToUInt32($b,$pos+60)
        $entries += [PSCustomObject]@{ Name=$nm; Off=$off; Size=$sz }
        $pos += 64
    }
    # Build new data: header + dir + data
    $newData = New-Object System.IO.MemoryStream
    $bw = New-Object System.IO.BinaryWriter($newData)
    $bw.Write($count)
    foreach($e in $entries){
        $nameBytes = [System.Text.Encoding]::ASCII.GetBytes($e.Name)
        $nb = New-Object byte[] 56
        [Array]::Copy($nameBytes, $nb, [Math]::Min($nameBytes.Length, 56))
        $bw.Write($nb)
        $bw.Write([UInt32]0)  # placeholder off
        $bw.Write([UInt32]0)  # placeholder size
    }
    $dataStart = $newData.Position
    # write data (original data for non-uni, new for uni)
    $di = 0
    foreach($e in $entries){
        $isUni = $e.Name -match '\.uni$'
        $zhPath = Join-Path $work ($e.Name + '.bin')
        $dataBytes = $null
        if($isUni -and (Test-Path $zhPath)){
            $dataBytes = [System.IO.File]::ReadAllBytes($zhPath)
        } else {
            $dataBytes = New-Object byte[] $e.Size
            [Array]::Copy($b, $e.Off, $dataBytes, 0, $e.Size)
        }
        $offPos = 4 + $di*64 + 56
        $szPos  = $offPos + 4
        $curPos = $newData.Position
        $bw.Write($dataBytes)
        # patch offsets
        $newData.Position = $offPos
        $bw.Write([UInt32]$curPos)
        $bw.Write([UInt32]$dataBytes.Length)
        $newData.Position = $newData.Length
        $di++
    }
    $bw.Flush()
    [System.IO.File]::WriteAllBytes($gtext, $newData.ToArray())
    Write-Output ("REBUILT gtext.lmp: {0} entries, new size {1}" -f $count, $newData.Length)
}
elseif($Step -eq 'gob'){
    # Rebuild each .gob: inner .lmp files may change size -> rebuild gob dir too.
    # For now: rebuild only gob-internal lmp files that contain uni, in place, then rebuild gob with new sizes.
    $gobs = Get-ChildItem -LiteralPath $res -Recurse -File -Filter '*.gob'
    foreach($gob in $gobs){
        $gb = [System.IO.File]::ReadAllBytes($gob.FullName)
        # parse gob dir (40-byte entries)
        $gents = @()
        $pos = 0
        while($pos + 40 -le $gb.Length){
            $nb = New-Object System.Collections.Generic.List[byte]
            for($k=0;$k -lt 32;$k++){ if($gb[$pos+$k] -eq 0){ break }; [void]$nb.Add($gb[$pos+$k]) }
            $nm = [System.Text.Encoding]::ASCII.GetString($nb.ToArray())
            if($nm -eq ''){ break }
            $off = [BitConverter]::ToUInt32($gb,$pos+32)
            $sz  = [BitConverter]::ToUInt32($gb,$pos+36)
            if($off + $sz -gt $gb.Length -or $sz -eq 0){ break }
            $gents += [PSCustomObject]@{ Name=$nm; Off=$off; Size=$sz }
            $pos += 40
        }
        if($gents.Count -eq 0){ continue }
        # rebuild each inner lmp that contains uni entries (requires new binary)
        $changed = @()
        foreach($ge in $gents){
            if($ge.Name -notmatch '\.lmp$'){ continue }
            $lmp = New-Object byte[] $ge.Size
            [Array]::Copy($gb, $ge.Off, $lmp, 0, $ge.Size)
            if($lmp.Length -lt 4){ continue }
            $lc = [BitConverter]::ToUInt32($lmp,0)
            if($lc -lt 1 -or $lc -gt 2000){ continue }
            # check if it has .uni entries with zh
            $hasZh = $false
            $lpos = 4
            for($i=0;$i -lt $lc;$i++){
                $lb = New-Object System.Collections.Generic.List[byte]
                for($k=0;$k -lt 56;$k++){ if($lmp[$lpos+$k] -eq 0){ break }; [void]$lb.Add($lmp[$lpos+$k]) }
                $lnm = [System.Text.Encoding]::ASCII.GetString($lb.ToArray())
                if($lnm -match '\.uni$'){
                    $zhPath = Join-Path $work ($lnm + '.bin')
                    if(Test-Path $zhPath){ $hasZh = $true; break }
                }
                $lpos += 64
            }
            if(-not $hasZh){ continue }
            # rebuild lmp
            $newLmp = New-Object System.IO.MemoryStream
            $bwl = New-Object System.IO.BinaryWriter($newLmp)
            $bwl.Write($lc)
            $lpos2 = 4
            $lEntries = @()
            for($i=0;$i -lt $lc;$i++){
                $lb = New-Object System.Collections.Generic.List[byte]
                for($k=0;$k -lt 56;$k++){ if($lmp[$lpos2+$k] -eq 0){ break }; [void]$lb.Add($lmp[$lpos2+$k]) }
                $lnm = [System.Text.Encoding]::ASCII.GetString($lb.ToArray())
                $loff = [BitConverter]::ToUInt32($lmp,$lpos2+56)
                $lsz  = [BitConverter]::ToUInt32($lmp,$lpos2+60)
                $lEntries += [PSCustomObject]@{ Name=$lnm; Off=$loff; Size=$lsz }
                $lpos2 += 64
            }
            foreach($le in $lEntries){
                $nameBytes = [System.Text.Encoding]::ASCII.GetBytes($le.Name)
                $nb = New-Object byte[] 56
                [Array]::Copy($nameBytes, $nb, [Math]::Min($nameBytes.Length, 56))
                $bwl.Write($nb)
                $bwl.Write([UInt32]0)
                $bwl.Write([UInt32]0)
            }
            $di2 = 0
            foreach($le in $lEntries){
                $zhPath = Join-Path $work ($le.Name + '.bin')
                $dataBytes = $null
                if($le.Name -match '\.uni$' -and (Test-Path $zhPath)){
                    $dataBytes = [System.IO.File]::ReadAllBytes($zhPath)
                } else {
                    $dataBytes = New-Object byte[] $le.Size
                    [Array]::Copy($lmp, $le.Off, $dataBytes, 0, $le.Size)
                }
                $offP = 4 + $di2*64 + 56
                $szP  = $offP + 4
                $cur = $newLmp.Position
                $bwl.Write($dataBytes)
                $newLmp.Position = $offP
                $bwl.Write([UInt32]$cur)
                $bwl.Write([UInt32]$dataBytes.Length)
                $newLmp.Position = $newLmp.Length
                $di2++
            }
            $bwl.Flush()
            $changed += [PSCustomObject]@{ Name=$ge.Name; OldOff=$ge.Off; OldSize=$ge.Size; NewData=$newLmp.ToArray() }
        }
        if($changed.Count -eq 0){ continue }
        # rebuild gob: header dir (unchanged names) + all data
        $newGob = New-Object System.IO.MemoryStream
        $bwg = New-Object System.IO.BinaryWriter($newGob)
        foreach($ge in $gents){
            $nameBytes = [System.Text.Encoding]::ASCII.GetBytes($ge.Name)
            $nb = New-Object byte[] 32
            [Array]::Copy($nameBytes, $nb, [Math]::Min($nameBytes.Length, 32))
            $bwg.Write($nb)
            $bwg.Write([UInt32]0)
            $bwg.Write([UInt32]0)
        }
        $di3 = 0
        foreach($ge in $gents){
            $chg = $changed | Where-Object { $_.Name -eq $ge.Name } | Select-Object -First 1
            if($chg){
                $dataBytes = $chg.NewData
            } else {
                $dataBytes = New-Object byte[] $ge.Size
                [Array]::Copy($gb, $ge.Off, $dataBytes, 0, $ge.Size)
            }
            $offP = $di3*40 + 32
            $szP  = $offP + 4
            $cur = $newGob.Position
            $bwg.Write($dataBytes)
            $newGob.Position = $offP
            $bwg.Write([UInt32]$cur)
            $bwg.Write([UInt32]$dataBytes.Length)
            $newGob.Position = $newGob.Length
            $di3++
        }
        $bwg.Flush()
        [System.IO.File]::WriteAllBytes($gob.FullName, $newGob.ToArray())
        Write-Output ("REBUILT {0}: {1} changed lmp, new gob size {2}" -f $gob.Name, $changed.Count, $newGob.Length)
    }
}
else {
    Write-Output "Usage: rebuild_uni.ps1 -Step encode|lmp|gob"
}