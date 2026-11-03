# verify_uni_roundtrip2.ps1 - ordered dict, compare by key
$ErrorActionPreference = 'Stop'
$res = Get-Item -LiteralPath 'E:\Game\ps5\iso\[XBOX].Baldur''s.Gate.Dark.Alliance.[USA]\res'
$b = [System.IO.File]::ReadAllBytes((Join-Path $res.FullName 'gtext.lmp'))
$count = [BitConverter]::ToUInt32($b,0)
$pos = 4
$entries = @()
for($i=0;$i -lt $count;$i++){
    $nb = New-Object System.Collections.Generic.List[byte]
    for($k=0;$k -lt 56;$k++){ if($b[$pos+$k] -eq 0){ break }; [void]$nb.Add($b[$pos+$k]) }
    $nm = [System.Text.Encoding]::ASCII.GetString($nb.ToArray())
    $off = [BitConverter]::ToUInt32($b,$pos+56)
    $sz  = [BitConverter]::ToUInt32($b,$pos+60)
    $entries += [PSCustomObject]@{ Name=$nm; Off=$off; Size=$sz }
    $pos += 64
}

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

function Build-Uni($dict){
    $ms = New-Object System.IO.MemoryStream
    $bw = New-Object System.IO.BinaryWriter($ms)
    foreach($k in $dict.Keys){
        $keyBytes = [System.Text.Encoding]::ASCII.GetBytes($k)
        $bw.Write($keyBytes)
        $bw.Write([byte]0)
        if(($keyBytes.Length % 2) -eq 0){ $bw.Write([byte]0) }
        $txt = $dict[$k]
        $txtBytes = [System.Text.Encoding]::Unicode.GetBytes($txt)
        $bw.Write($txtBytes)
        $bw.Write([byte]0); $bw.Write([byte]0)
    }
    $bw.Flush()
    return $ms.ToArray()
}

foreach($target in @('gtext.uni','gtext_ja.uni','gtext_fr.uni')){
    $e = $entries | Where-Object { $_.Name -eq $target } | Select-Object -First 1
    $data = New-Object byte[] $e.Size
    [Array]::Copy($b, $e.Off, $data, 0, $e.Size)
    $parsed = Parse-Uni $data
    Write-Output ("=== {0}: orig {1} bytes, {2} entries ===" -f $target, $e.Size, $parsed.Count)
    # ordered dict preserve original order
    $od = New-Object 'System.Collections.Specialized.OrderedDictionary'
    foreach($p in $parsed){ $od[$p.Key] = $p.Text }
    $newBin = Build-Uni $od
    $reparsed = Parse-Uni $newBin
    Write-Output ("    rebuilt {0} bytes, re-parsed {1} entries" -f $newBin.Length, $reparsed.Count)
    # compare by key order
    $keyMatch = 0; $textDiff = 0
    for($i=0;$i -lt [Math]::Min($parsed.Count,$reparsed.Count);$i++){
        if($parsed[$i].Key -eq $reparsed[$i].Key){ $keyMatch++ }
        if($parsed[$i].Key -eq $reparsed[$i].Key -and $parsed[$i].Text -ne $reparsed[$i].Text){ 
            if($textDiff -lt 3){ Write-Output ("    TEXT DIFF [{0}]: orig='{1}' new='{2}'" -f $parsed[$i].Key, $parsed[$i].Text, $reparsed[$i].Text) }
            $textDiff++ 
        }
    }
    Write-Output ("    key-order match {0}/{1}, text diffs {2}" -f $keyMatch, $parsed.Count, $textDiff)
    if($parsed.Count -ne $reparsed.Count){
        # find where they diverge
        $d = -1
        for($i=0;$i -lt [Math]::Min($parsed.Count,$reparsed.Count);$i++){
            if($parsed[$i].Key -ne $reparsed[$i].Key){ $d = $i; break }
        }
        Write-Output ("    first divergence at index {0}: orig='{1}' new='{2}'" -f $d, $(if($d -ge 0){$parsed[$d].Key}else{'n/a'}), $(if($d -ge 0){$reparsed[$d].Key}else{'n/a'}))
        # tail of original
        if($parsed.Count -gt $reparsed.Count){
            Write-Output ("    original tail keys: " + (($parsed[$reparsed.Count..($parsed.Count-1)] | ForEach-Object { $_.Key }) -join ', '))
        } else {
            Write-Output ("    rebuilt tail keys: " + (($reparsed[$parsed.Count..($reparsed.Count-1)] | ForEach-Object { $_.Key }) -join ', '))
        }
    }
    Write-Output ""
}