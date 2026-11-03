# diag_uni.ps1 (ASCII only) - dump original & rebuilt uni bytes to compare format
$ErrorActionPreference = 'Stop'
$res = Get-Item -LiteralPath 'E:\Game\ps5\iso\[XBOX].Baldur''s.Gate.Dark.Alliance.[USA]\res'
$b = [System.IO.File]::ReadAllBytes((Join-Path $res.FullName 'gtext.lmp'))
$count = [BitConverter]::ToUInt32($b,0)
$pos = 4
$e = $null
for($i=0;$i -lt $count;$i++){
    $nb = New-Object System.Collections.Generic.List[byte]
    for($k=0;$k -lt 56;$k++){ if($b[$pos+$k] -eq 0){ break }; [void]$nb.Add($b[$pos+$k]) }
    $nm = [System.Text.Encoding]::ASCII.GetString($nb.ToArray())
    $off = [BitConverter]::ToUInt32($b,$pos+56)
    $sz  = [BitConverter]::ToUInt32($b,$pos+60)
    if($nm -eq 'gtext.uni'){ $e = [PSCustomObject]@{ Name=$nm; Off=$off; Size=$sz }; break }
    $pos += 64
}
Write-Output ("gtext.uni @ {0}, size {1}" -f $e.Off, $e.Size)
$data = New-Object byte[] $e.Size
[Array]::Copy($b, $e.Off, $data, 0, $e.Size)
Write-Output "=== ORIGINAL gtext.uni first 128 bytes ==="
for($o=0;$o -lt 128;$o+=16){
    $row = $data[$o..($o+15)]
    $hex = ($row | ForEach-Object { $_.ToString('X2') }) -join ' '
    $ascii = -join ($row | ForEach-Object { if($_ -ge 32 -and $_ -le 126){[char]$_}else{'.'} })
    Write-Output ("{0:X4}: {1,-47} {2}" -f $o, $hex, $ascii)
}
Write-Output ""
Write-Output "=== search entry boundaries: find 00 00 pattern after ascii keys ==="
# find position of last key end + 2 (text start) for first 5 entries
$p2 = 0
for($i2=0;$i2 -lt 5;$i2++){
    $ks = $p2
    while($p2 -lt $data.Length -and $data[$p2] -ne 0){ $p2++ }
    $key = [System.Text.Encoding]::ASCII.GetString($data[$ks..($p2-1)])
    Write-Output ("entry {0}: key='{1}' (ends@{2:X}), bytes after: {3} {4}" -f $i2, $key, $p2, $data[$p2].ToString('X2'), $data[$p2+1].ToString('X2'))
    # text start: key end + 2
    $tStart = $p2 + 2
    $tEnd = $tStart
    while($tEnd + 1 -lt $data.Length -and -not ($data[$tEnd] -eq 0 -and $data[$tEnd+1] -eq 0)){ $tEnd += 2 }
    $txt = [System.Text.Encoding]::Unicode.GetString($data[$tStart..($tEnd-1)])
    Write-Output ("      text@{2:X}: '{0}' (next key@{1:X})" -f $txt.Substring(0,[Math]::Min(30,$txt.Length)), ($tEnd+2), $tStart)
    $p2 = $tEnd + 2
}