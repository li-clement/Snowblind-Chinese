$ErrorActionPreference = 'Stop'
$root = 'E:\Game\ps5\iso\[XBOX].Baldur''s.Gate.Dark.Alliance.[USA]'
$b = [System.IO.File]::ReadAllBytes((Join-Path $root 'default.xbe'))

function Find-U16Runs([byte[]]$b, [int]$minLen) {
    $runs = @(); $run = 0; $start = -1
    for ($i = 0; $i -lt $b.Length - 1; $i += 2) {
        $c = $b[$i]; $n = $b[$i + 1]
        if ($c -ge 0x20 -and $c -le 0x7E -and $n -eq 0) {
            if ($run -eq 0) { $start = $i }
            $run++
        } else {
            if ($run -ge $minLen) { $runs += [PSCustomObject]@{ Pos = $start; Len = $run } }
            $run = 0
        }
    }
    if ($run -ge $minLen) { $runs += [PSCustomObject]@{ Pos = $start; Len = $run } }
    return $runs
}

$runs = Find-U16Runs $b 30
Write-Output "XBE 中 UTF-16 串(>=30 字符)数量: $($runs.Count)"
$sample = 0
foreach($r in $runs){ if($sample -ge 15){ break }; $end = [Math]::Min($r.Pos + $r.Len*2 - 1, $b.Length-1); $s = [System.Text.Encoding]::Unicode.GetString($b[$r.Pos..$end]); Write-Output ("  @0x{0:X} [{1}]: {2}" -f $r.Pos, $r.Len, $s.Substring(0,[Math]::Min(80,$s.Length))); $sample++ }