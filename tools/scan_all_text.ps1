param(
    [string]$ResDir = 'E:\Game\ps5\iso\[XBOX].Baldur''s.Gate.Dark.Alliance.[USA]\res'
)
$ErrorActionPreference = 'Stop'

function Parse-LmpEntries([byte[]]$b) {
    $count = [BitConverter]::ToInt32($b, 0)
    if ($count -lt 1 -or $count -gt 500) { return @() }
    $pos = 4
    $entries = @()
    for ($i = 0; $i -lt $count; $i++) {
        if ($pos + 64 -gt $b.Length) { break }
        $nb = New-Object System.Collections.Generic.List[byte]
        $nl = 0
        while ($nl -lt 56 -and $b[$pos + $nl] -ne 0) { [void]$nb.Add($b[$pos + $nl]); $nl++ }
        $nm = [System.Text.Encoding]::ASCII.GetString($nb.ToArray())
        $off = [BitConverter]::ToInt32($b, $pos + 56)
        $sz  = [BitConverter]::ToInt32($b, $pos + 60)
        $pos += 64
        if ($off -ge 0 -and $off + $sz -le $b.Length -and $sz -gt 0) {
            $entries += [PSCustomObject]@{ Name = $nm; Off = $off; Size = $sz }
        }
    }
    return $entries
}

function Get-AsciiRuns([byte[]]$b, [int]$minLen) {
    $runs = @(); $run = 0; $start = -1
    for ($i = 0; $i -lt $b.Length; $i++) {
        $c = $b[$i]
        if ($c -ge 0x20 -and $c -le 0x7E) {
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

function Get-U16Runs([byte[]]$b, [int]$minLen) {
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

$lmpFiles = Get-ChildItem -LiteralPath $ResDir -Recurse -File -Filter '*.lmp'
$reportAscii = @()
$reportU16 = @()
foreach ($lf in $lmpFiles) {
    $b = [System.IO.File]::ReadAllBytes($lf.FullName)
    if ($b.Length -lt 8) { continue }
    $entries = Parse-LmpEntries $b
    if ($entries.Count -eq 0) { continue }
    foreach ($e in $entries) {
        $data = New-Object byte[] $e.Size
        [Array]::Copy($b, $e.Off, $data, 0, $e.Size)
        $ar = Get-AsciiRuns $data 40
        if ($ar.Count -gt 0) {
            $best = $ar | Sort-Object Len -Descending | Select-Object -First 1
            $s = [System.Text.Encoding]::ASCII.GetString($data[$best.Pos..($best.Pos + [Math]::Min($best.Len, 80) - 1)])
            $reportAscii += [PSCustomObject]@{ Parent = $lf.Name; Sub = $e.Name; Size = $e.Size; MaxRun = $best.Len; Sample = $s }
        }
        $u16 = Get-U16Runs $data 20
        if ($u16.Count -gt 0) {
            $bestU = $u16 | Sort-Object Len -Descending | Select-Object -First 1
            $end = [Math]::Min($bestU.Pos + $bestU.Len * 2 - 1, $data.Length - 1)
            $su = [System.Text.Encoding]::Unicode.GetString($data[$bestU.Pos..$end])
            $reportU16 += [PSCustomObject]@{ Parent = $lf.Name; Sub = $e.Name; Size = $e.Size; MaxRun = $bestU.Len; Sample = $su.Substring(0, [Math]::Min(80, $su.Length)) }
        }
    }
}
Write-Output "=== ASCII runs >= 40 (excl. known binary types) ==="
$reportAscii | Where-Object { $_.Sub -notmatch '\.(tex|anm|vif|wav|vag|m2v|xmv|ico|fnt|vat|va1)$' } | Sort-Object MaxRun -Descending | Select-Object -First 60 Parent, Sub, Size, MaxRun, Sample | Format-Table -AutoSize -Wrap
Write-Output ""
Write-Output "=== U16 runs >= 20 (excl. gtext) ==="
$reportU16 | Where-Object { $_.Parent -ne 'gtext.lmp' -and $_.Sub -notmatch '\.(tex|anm|vif|wav|vag|m2v|xmv|ico|fnt|vat|va1)$' } | Sort-Object MaxRun -Descending | Select-Object -First 40 Parent, Sub, Size, MaxRun, Sample | Format-Table -AutoSize -Wrap