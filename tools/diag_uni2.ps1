# diag_uni2.ps1 (ASCII only) - precise boundary scan of original gtext.uni
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

# entry 0: key controllerOutMsg ends@0x10, byte@0x10=00, text starts@0x11? or 0x12?
Write-Output "=== entry0 raw bytes @0x0E-0x18 ==="
for($o=0x0E;$o -le 0x18;$o++){
    $ch = '.'
    if($data[$o] -ge 32 -and $data[$o] -le 126){ $ch = [char]$data[$o] }
    Write-Output ("  @{0:X2}: {1} '{2}'" -f $o, $data[$o].ToString('X2'), $ch)
}
Write-Output ("entry0 text from 0x11 (UTF16): {0}" -f [System.Text.Encoding]::Unicode.GetString($data[0x11..0x1F]))
Write-Output ("entry0 text from 0x12 (UTF16): {0}" -f [System.Text.Encoding]::Unicode.GetString($data[0x12..0x20]))

# Hypothesis A: key + 00 + utf16 text (no alignment). parse all entries this way, count
Write-Output ""
Write-Output "=== Hypothesis A: key+00+text, text until 00 00 ==="
$pa = 0; $nA = 0; $examples = @()
while($pa + 2 -lt $len){
    $ks = $pa
    while($pa -lt $len -and $data[$pa] -ne 0){ $pa++ }
    if($pa -ge $len){ break }
    if($pa -eq $ks){ $pa++; continue }  # empty key skip
    $key = [System.Text.Encoding]::ASCII.GetString($data[$ks..($pa-1)])
    $pa++  # skip 00
    $ts = $pa
    while($pa + 1 -lt $len -and -not ($data[$pa] -eq 0 -and $data[$pa+1] -eq 0)){ $pa += 2 }
    $txt = ''
    if($pa -ge $ts){ $txt = [System.Text.Encoding]::Unicode.GetString($data[$ts..($pa-1)]) }
    if($nA -lt 3){ $examples += ("[{0}] '{1}'" -f $key, $txt.Substring(0,[Math]::Min(40,$txt.Length))) }
    $nA++
    $pa += 2
}
Write-Output ("count A: {0}" -f $nA)
$examples | ForEach-Object { Write-Output ("  {0}" -f $_) }

# Hypothesis B: key + 00 + 00 + utf16 text
Write-Output ""
Write-Output "=== Hypothesis B: key+00+00+text ==="
$pb = 0; $nB = 0; $exB = @()
while($pb + 2 -lt $len){
    $ks = $pb
    while($pb -lt $len -and $data[$pb] -ne 0){ $pb++ }
    if($pb -ge $len){ break }
    if($pb -eq $ks){ $pb = $pb + 2; continue }
    $key = [System.Text.Encoding]::ASCII.GetString($data[$ks..($pb-1)])
    $pb += 2  # skip 00 00
    $ts = $pb
    while($pb + 1 -lt $len -and -not ($data[$pb] -eq 0 -and $data[$pb+1] -eq 0)){ $pb += 2 }
    $txt = ''
    if($pb -ge $ts){ $txt = [System.Text.Encoding]::Unicode.GetString($data[$ts..($pb-1)]) }
    if($nB -lt 3){ $exB += ("[{0}] '{1}'" -f $key, $txt.Substring(0,[Math]::Min(40,$txt.Length))) }
    $nB++
    $pb += 2
}
Write-Output ("count B: {0}" -f $nB)
$exB | ForEach-Object { Write-Output ("  {0}" -f $_) }

# Hypothesis C: key + 00 + utf16 text, text ends at 00 00 followed by next ascii key.
# Actually A and B differ only by 1 byte alignment per entry. Check total bytes consumed.
Write-Output ""
Write-Output "total uni size: $len"
$consumedA = $pa
$consumedB = $pb
Write-Output "consumed A (end pos): $consumedA"
Write-Output "consumed B (end pos): $consumedB"
Write-Output ("A tail bytes: " + (($data[($consumedA)..([Math]::Min($consumedA+7,$len-1))] | ForEach-Object { $_.ToString('X2') }) -join ' '))
Write-Output ("B tail bytes: " + (($data[($consumedB)..([Math]::Min($consumedB+7,$len-1))] | ForEach-Object { $_.ToString('X2') }) -join ' '))