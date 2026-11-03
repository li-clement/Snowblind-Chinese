# extract_all_uni.ps1 (ASCII only)
$ErrorActionPreference = 'Stop'
$res = Get-Item -LiteralPath 'E:\Game\ps5\iso\[XBOX].Baldur''s.Gate.Dark.Alliance.[USA]\res'
$outDir = 'E:\Game\ps5\iso\translation'
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

function Try-Parse([byte[]]$b, [int]$nameSz, [int]$metaOff, [int]$startOff, [int]$stride){
    $entries = New-Object System.Collections.Generic.List[object]
    $pos = $startOff
    $max = $b.Length - 1
    $guard = 0
    while($pos + $nameSz + 8 -le $max -and $guard -lt 1024){
        $nameOk = $true
        for($k=0; $k -lt $nameSz; $k++){
            $c = $b[$pos+$k]
            if($c -eq 0){ break }
            if($c -lt 32 -or $c -gt 126){ $nameOk = $false; break }
        }
        if(-not $nameOk){ break }
        $nb = New-Object System.Collections.Generic.List[byte]
        for($k=0; $k -lt $nameSz; $k++){
            if($b[$pos+$k] -eq 0){ break }
            [void]$nb.Add($b[$pos+$k])
        }
        $nm = [System.Text.Encoding]::ASCII.GetString($nb.ToArray())
        if($nm -eq ''){ break }
        $off = [BitConverter]::ToUInt32($b, ($pos + $nameSz + $metaOff))
        $sz  = [BitConverter]::ToUInt32($b, ($pos + $nameSz + $metaOff + 4))
        if($off -ge 0 -and $off + $sz -le $b.Length -and $sz -gt 0 -and $sz -lt 50MB){
            $entries.Add([PSCustomObject]@{ Name=$nm; Off=$off; Size=$sz })
        } else {
            $off = [BitConverter]::ToUInt32($b, ($pos + $nameSz))
            $sz  = [BitConverter]::ToUInt32($b, ($pos + $nameSz + 4))
            if($off -ge 0 -and $off + $sz -le $b.Length -and $sz -gt 0 -and $sz -lt 50MB){
                $entries.Add([PSCustomObject]@{ Name=$nm; Off=$off; Size=$sz })
            } else {
                $entries.Clear(); break
            }
        }
        $pos += $stride
        $guard++
    }
    return $entries
}

function Parse-Best([byte[]]$b){
    $cands = @(
        @(56, 0, 0, 64),
        @(56, 0, 4, 64),
        @(40, 0, 0, 48),
        @(40, 0, 4, 48),
        @(32, 0, 0, 40),
        @(32, 0, 4, 40),
        @(45, 0, 0, 53),
        @(60, 0, 0, 68)
    )
    $best = $null
    $bestCount = 0
    $bestCfg = $null
    foreach($c in $cands){
        $e = Try-Parse $b $c[0] $c[1] $c[2] $c[3]
        if($e.Count -gt $bestCount){ $best = $e; $bestCount = $e.Count; $bestCfg = $c }
    }
    return @{ Entries = $best; Cfg = $bestCfg }
}

function Parse-Uni([byte[]]$d){
    $items = New-Object System.Collections.Generic.List[object]
    $pos = 0
    $len = $d.Length
    while($pos + 4 -lt $len){
        $kStart = $pos
        while($pos -lt $len -and $d[$pos] -ne 0){ $pos++ }
        if($pos -ge $len){ break }
        $key = [System.Text.Encoding]::ASCII.GetString($d[$kStart..($pos-1)])
        $pos++
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

Write-Output '=== [1/2] gtext.lmp ==='
$g = [System.IO.File]::ReadAllBytes((Join-Path $res.FullName 'gtext.lmp'))
$gp = Parse-Best $g
Write-Output ("gtext.lmp parsed: {0} entries (cfg name{1} meta+{2} start{3} stride{4})" -f $gp.Entries.Count, $gp.Cfg[0], $gp.Cfg[1], $gp.Cfg[2], $gp.Cfg[3])
$all = New-Object System.Collections.Generic.List[object]
foreach($e in $gp.Entries){
    if($e.Name -match '^gtext.*\.uni$'){
        $data = New-Object byte[] $e.Size
        [Array]::Copy($g, $e.Off, $data, 0, $e.Size)
        $items = Parse-Uni $data
        Write-Output ("  {0}: {1} entries" -f $e.Name, $items.Count)
        foreach($it in $items){
            $all.Add([PSCustomObject]@{ Source='gtext.lmp'; File=$e.Name; Key=$it.Key; En=$it.Text; Zh='' })
        }
    }
}

Write-Output '=== [2/2] .gob files ==='
$gobs = Get-ChildItem -LiteralPath $res.FullName -Recurse -File -Filter '*.gob'
foreach($gob in $gobs){
    $b = [System.IO.File]::ReadAllBytes($gob.FullName)
    $p = Parse-Best $b
    if($p.Entries.Count -eq 0){ Write-Output ("  {0}: no dir" -f $gob.Name); continue }
    $unis = $p.Entries | Where-Object { $_.Name -match '\.uni$' -and $_.Name -notmatch '^_' }
    if($unis.Count -gt 0){
        Write-Output ("  {0}: {1} entries, uni {2}" -f $gob.Name, $p.Entries.Count, $unis.Count)
    }
    foreach($e in $unis){
        $data = New-Object byte[] $e.Size
        [Array]::Copy($b, $e.Off, $data, 0, $e.Size)
        $items = Parse-Uni $data
        foreach($it in $items){
            $all.Add([PSCustomObject]@{ Source=$gob.Name; File=$e.Name; Key=$it.Key; En=$it.Text; Zh='' })
        }
    }
}

Write-Output ("`nTotal entries (all langs): {0}" -f $all.Count)
Write-Output ("Unique keys: {0}" -f (($all | Select-Object -ExpandProperty Key -Unique).Count))

$enBase = $all | Where-Object { $_.File -match '\.uni$' }
Write-Output ("EN-base entries: {0}" -f $enBase.Count)

$all | ConvertTo-Json -Depth 3 | Set-Content -LiteralPath (Join-Path $outDir 'all_text.json') -Encoding UTF8
$all | Where-Object { $_.En -ne '' -or $_.Key -ne '' } | Select-Object Source, File, Key, En, Zh |
    Export-Csv -LiteralPath (Join-Path $outDir 'translation_table.csv') -NoTypeInformation -Encoding UTF8
Write-Output ("CSV: {0}" -f (Join-Path $outDir 'translation_table.csv'))

$enOnly = $enBase | Where-Object { $_.En -ne '' } | Select-Object -Unique Source, File, Key, En
$sb = New-Object System.Text.StringBuilder
foreach($r in $enOnly){
    $esc = $r.En -replace '[\r\n]+', ' / '
    [void]$sb.AppendLine("[$($r.Source)|$($r.File)|$($r.Key)]")
    [void]$sb.AppendLine("EN: $esc")
    [void]$sb.AppendLine("ZH: ")
    [void]$sb.AppendLine()
}
Set-Content -LiteralPath (Join-Path $outDir 'en_texts.txt') -Value $sb.ToString() -Encoding UTF8
Write-Output ("TXT: en_texts.txt ({0} entries)" -f $enOnly.Count)