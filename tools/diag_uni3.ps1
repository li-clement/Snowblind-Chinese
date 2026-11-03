# diag_uni3.ps1 - dump exact bytes around entry0/entry1 boundary
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
$data = New-Object byte[] $e.Size
[Array]::Copy($b, $e.Off, $data, 0, $e.Size)
$len = $data.Length

function Dump([int]$s, [int]$n){
    for($o=$s;$o -lt $s+$n;$o+=16){
        $e2 = [Math]::Min($o+15,$len-1)
        $row = $data[$o..$e2]
        $hex = ($row | ForEach-Object { $_.ToString('X2') }) -join ' '
        $asc = -join ($row | ForEach-Object { if($_ -ge 32 -and $_ -le 126){[char]$_}else{'.'} })
        Write-Output ("{0:X4}: {1,-47} {2}" -f $o, $hex, $asc)
    }
}

Write-Output "=== entry0 key+terminator region 0x08-0x20 ==="
Dump 0x08 24
Write-Output ""
Write-Output "=== find entry1 key start: search 'controllerPressStartMsg' ==="
$idx = [System.Text.Encoding]::ASCII.GetBytes('controllerPressStartMsg')
$found = -1
for($i=0;$i -lt $len - $idx.Length; $i++){
    $ok = $true
    for($j=0;$j -lt $idx.Length;$j++){ if($data[$i+$j] -ne $idx[$j]){ $ok=$false; break } }
    if($ok){ $found = $i; break }
}
Write-Output ("controllerPressStartMsg found at 0x{0:X}" -f $found)
Write-Output ""
Write-Output "=== around entry1 key (0x100-0x140) ==="
Dump ([Math]::Max(0,$found-16)) 80
Write-Output ""
Write-Output "=== entry0 text end: search 'continue.' ==="
$cont = [System.Text.Encoding]::ASCII.GetBytes('continue.')
$found2 = -1
for($i=0;$i -lt $len - $cont.Length; $i++){
    $ok = $true
    for($j=0;$j -lt $cont.Length;$j++){ if($data[$i+$j] -ne $cont[$j]){ $ok=$false; break } }
    if($ok){ $found2 = $i; break }
}
Write-Output ("'continue.' found at 0x{0:X}, dump 0x{0:X}-0x{1:X}" -f $found2, ($found2+32))
Dump $found2 40