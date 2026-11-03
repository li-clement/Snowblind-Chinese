$ErrorActionPreference = 'Stop'
$res = Get-Item -LiteralPath 'E:\Game\ps5\iso\[XBOX].Baldur''s.Gate.Dark.Alliance.[USA]\res'
$gname = 'tavern.gob'
$b = [System.IO.File]::ReadAllBytes((Join-Path $res.FullName $gname))
$count = [BitConverter]::ToInt32($b, 0)
Write-Output "$gname head bytes: $(($b[0..7] | ForEach-Object { $_.ToString('X2') }) -join ' ')"
Write-Output "entry count @0: $count"
$pos = 4
$entries = @()
for($i=0; $i -lt $count; $i++){
    if($pos + 64 -gt $b.Length){ break }
    $nb = New-Object System.Collections.Generic.List[byte]
    $nl = 0
    while($nl -lt 56 -and $b[$pos+$nl] -ne 0){ [void]$nb.Add($b[$pos+$nl]); $nl++ }
    $nm = [System.Text.Encoding]::ASCII.GetString($nb.ToArray())
    $off = [BitConverter]::ToInt32($b, $pos+56)
    $sz  = [BitConverter]::ToInt32($b, $pos+60)
    $entries += [PSCustomObject]@{ Idx=$i; Name=$nm; Off=$off; Size=$sz }
    $pos += 64
}
Write-Output "=== 解析出的条目($($entries.Count)) ==="
$entries | Format-Table Idx, Name, Off, Size -AutoSize | Out-String -Width 120
Write-Output "=== uni 条目及其数据验证 ==="
$entries | Where-Object { $_.Name -match '\.uni$' } | ForEach-Object {
    $e = $_
    $valid = ($e.Off -ge 0 -and $e.Off + $e.Size -le $b.Length)
    $sample = ''
    if($valid){
        $d = New-Object byte[] $e.Size
        [Array]::Copy($b, $e.Off, $d, 0, $e.Size)
        $u = [System.Text.Encoding]::Unicode.GetString($d[0..([Math]::Min(39,$d.Length-1))])
        $sample = $u -replace '[^\x20-\x7E]', '.'
    }
    Write-Output ("  {0,-14} off=0x{1:X6} size={2,7} valid={3} start={4}" -f $e.Name, $e.Off, $e.Size, $valid, $sample)
}