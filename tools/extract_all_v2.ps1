# extract_all_v2.ps1 (ASCII only) - full pipeline: .gob -> .lmp -> .uni
$ErrorActionPreference = 'Stop'
$res = Get-Item -LiteralPath 'E:\Game\ps5\iso\[XBOX].Baldur''s.Gate.Dark.Alliance.[USA]\res'
$outDir = 'E:\Game\ps5\iso\translation'
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

# ---- .gob: 32-byte name + u32 off + u32 size, stride 40, start at 0 ----
function Parse-Gob([byte[]]$b){
    $entries = New-Object System.Collections.Generic.List[object]
    $pos = 0
    $guard = 0
    while($pos + 40 -le $b.Length -and $guard -lt 2000){
        $nb = New-Object System.Collections.Generic.List[byte]
        for($k=0; $k -lt 32; $k++){
            $c = $b[$pos+$k]
            if($c -eq 0){ break }
            if($c -lt 32 -or $c -gt 126){ return $entries }  # bad name -> stop
            [void]$nb.Add($c)
        }
        $nm = [System.Text.Encoding]::ASCII.GetString($nb.ToArray())
        if($nm -eq ''){ break }
        $off = [BitConverter]::ToUInt32($b, $pos+32)
        $sz  = [BitConverter]::ToUInt32($b, $pos+36)
        if($off -lt 0 -or $off + $sz -gt $b.Length -or $sz -eq 0 -or $sz -gt 100MB){ break }
        $entries.Add([PSCustomObject]@{ Name=$nm; Off=$off; Size=$sz })
        $pos += 40
        $guard++
    }
    return $entries
}

# ---- .lmp: u32 count + name56 + off + size, stride 64, start at 4 ----
function Parse-Lmp([byte[]]$b){
    $entries = New-Object System.Collections.Generic.List[object]
    if($b.Length -lt 4){ return $entries }
    $count = [BitConverter]::ToUInt32($b, 0)
    if($count -lt 1 -or $count -gt 2000){ return $entries }
    $pos = 4
    for($i=0; $i -lt $count; $i++){
        if($pos + 64 -gt $b.Length){ break }
        $nb = New-Object System.Collections.Generic.List[byte]
        for($k=0; $k -lt 56; $k++){
            $c = $b[$pos+$k]
            if($c -eq 0){ break }
            if($c -lt 32 -or $c -gt 126){ return $entries }
            [void]$nb.Add($c)
        }
        $nm = [System.Text.Encoding]::ASCII.GetString($nb.ToArray())
        $off = [BitConverter]::ToUInt32($b, $pos+56)
        $sz  = [BitConverter]::ToUInt32($b, $pos+60)
        if($off -lt 0 -or $off + $sz -gt $b.Length -or $sz -eq 0 -or $sz -gt 100MB){ break }
        $entries.Add([PSCustomObject]@{ Name=$nm; Off=$off; Size=$sz })
        $pos += 64
    }
    return $entries
}

# ---- .uni: (ASCII key \0) + (align even) + (UTF-16LE text \0) repeated ----
function Parse-Uni([byte[]]$d){
    $items = New-Object System.Collections.Generic.List[object]
    $pos = 0
    $len = $d.Length
    while($pos + 4 -lt $len){
        $kStart = $pos
        while($pos -lt $len -and $d[$pos] -ne 0){ $pos++ }
        if($pos -ge $len){ break }
        $key = [System.Text.Encoding]::ASCII.GetString($d[$kStart..($pos-1)])
        if($key -eq ''){ break }
        $pos++  # skip key NUL
        if($pos % 2 -ne 0){ $pos++ }  # align to even (skip padding byte if odd)
        # text until 00 00
        $tStart = $pos
        while($pos + 1 -lt $len -and -not ($d[$pos] -eq 0 -and $d[$pos+1] -eq 0)){ $pos += 2 }
        $txt = ''
        if($pos - 1 -ge $tStart){
            $txt = [System.Text.Encoding]::Unicode.GetString($d[$tStart..($pos-1)])
        }
        $items.Add([PSCustomObject]@{ Key=$key; Text=$txt })
        $pos += 2
    }
    return $items
}

function Save-Bytes([byte[]]$d, [string]$path){
    [System.IO.File]::WriteAllBytes($path, $d)
}

$all = New-Object System.Collections.Generic.List[object]

# ===== pass 1: standalone .lmp in res (gtext.lmp, font.lmp, frontend.lmp etc.) =====
$topLmps = Get-ChildItem -LiteralPath $res.FullName -File -Filter '*.lmp'
foreach($f in $topLmps){
    $b = [System.IO.File]::ReadAllBytes($f.FullName)
    $ents = Parse-Lmp $b
    if($ents.Count -eq 0){ continue }
    $unis = @($ents | Where-Object { $_.Name -match '\.uni$' })
    if($unis.Count -eq 0){ continue }
    Write-Output ("standalone {0}: {1} entries, {2} uni" -f $f.Name, $ents.Count, $unis.Count)
    foreach($e in $unis){
        $data = New-Object byte[] $e.Size
        [Array]::Copy($b, $e.Off, $data, 0, $e.Size)
        $items = Parse-Uni $data
        foreach($it in $items){
            $all.Add([PSCustomObject]@{ Source=$f.Name; File=$e.Name; Key=$it.Key; En=$it.Text; Zh='' })
        }
    }
}

# ===== pass 2: .gob -> .lmp -> .uni =====
$gobs = Get-ChildItem -LiteralPath $res.FullName -Recurse -File -Filter '*.gob'
foreach($gob in $gobs){
    $gb = [System.IO.File]::ReadAllBytes($gob.FullName)
    $gents = Parse-Gob $gb
    if($gents.Count -eq 0){ Write-Output ("gob {0}: no entries" -f $gob.Name); continue }
    $foundLmp = 0; $foundUni = 0
    foreach($ge in $gents){
        if($ge.Name -notmatch '\.lmp$'){ continue }
        $lmp = New-Object byte[] $ge.Size
        [Array]::Copy($gb, $ge.Off, $lmp, 0, $ge.Size)
        $lents = Parse-Lmp $lmp
        if($lents.Count -eq 0){ continue }
        $foundLmp++
        foreach($le in $lents){
            if($le.Name -notmatch '\.uni$'){ continue }
            $foundUni++
            $data = New-Object byte[] $le.Size
            [Array]::Copy($lmp, $le.Off, $data, 0, $le.Size)
            $items = Parse-Uni $data
            foreach($it in $items){
                $all.Add([PSCustomObject]@{ Source=$gob.Name; File=$le.Name; Key=$it.Key; En=$it.Text; Zh='' })
            }
        }
    }
    if($foundUni -gt 0){
        Write-Output ("gob {0}: {1} lmps, {2} uni files" -f $gob.Name, $foundLmp, $foundUni)
    }
}

Write-Output ("`nTOTAL entries: {0}" -f $all.Count)
$enBase = $all | Where-Object { $_.File -match '\.uni$' }
Write-Output ("EN-base entries: {0}" -f $enBase.Count)
Write-Output ("Unique (Source+File+Key): {0}" -f (($all | ForEach-Object { "$($_.Source)|$($_.File)|$($_.Key)" } | Sort-Object -Unique).Count))

# Save full JSON
$all | ConvertTo-Json -Depth 3 | Set-Content -LiteralPath (Join-Path $outDir 'all_text_v2.json') -Encoding UTF8

# Save translation CSV (only English base: file exactly *.uni with no _xx suffix)
$enOnly = $all | Where-Object { $_.File -match '^[a-z0-9_]*\.uni$' -and $_.File -notmatch '_[a-z]{2}\.uni$' } |
    Select-Object Source, File, Key, En, Zh
$enOnly | Export-Csv -LiteralPath (Join-Path $outDir 'translation_en.csv') -NoTypeInformation -Encoding UTF8
Write-Output ("EN translation CSV: {0} rows" -f $enOnly.Count)

# Plain text list for translation
$sb = New-Object System.Text.StringBuilder
foreach($r in $enOnly){
    $esc = $r.En -replace '[\r\n]+', ' / '
    [void]$sb.AppendLine("[$($r.Source)|$($r.File)|$($r.Key)]")
    [void]$sb.AppendLine("EN: $esc")
    [void]$sb.AppendLine("ZH: ")
    [void]$sb.AppendLine()
}
Set-Content -LiteralPath (Join-Path $outDir 'en_texts_v2.txt') -Value $sb.ToString() -Encoding UTF8
Write-Output ("TXT written: en_texts_v2.txt")