# verify_uni_roundtrip3.ps1 - ordered list (allow duplicate keys), build from list
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

foreach($target in @('gtext.uni','gtext_ja.uni','gtext_fr.uni')){
    $e = $entries | Where-Object { $_.Name -eq $target } | Select-Object -First 1
    $data = New-Object byte[] $e.Size
    [Array]::Copy($b, $e.Off, $data, 0, $e.Size)
    $parsed = Parse-Uni $data
    $newBin = Build-UniFromList $parsed
    $reparsed = Parse-Uni $newBin
    Write-Output ("=== {0}: orig {1} bytes/{2} entries, rebuilt {3} bytes/{4} entries ===" -f $target, $e.Size, $parsed.Count, $newBin.Length, $reparsed.Count)
    $full = ($parsed.Count -eq $reparsed.Count)
    $allMatch = $true
    if($full){
        for($i=0;$i -lt $parsed.Count;$i++){
            if($parsed[$i].Key -ne $reparsed[$i].Key -or $parsed[$i].Text -ne $reparsed[$i].Text){ $allMatch = $false; Write-Output ("    DIFF@{0}: [{1}]'{2}' vs [{3}]'{4}'" -f $i, $parsed[$i].Key, $parsed[$i].Text, $reparsed[$i].Key, $reparsed[$i].Text); break }
        }
    }
    Write-Output ("    BYTE-IDENTICAL: {0}" -f ($newBin.Length -eq $e.Size))
    Write-Output ("    FULL MATCH: {0}" -f ($full -and $allMatch))
    Write-Output ""
}