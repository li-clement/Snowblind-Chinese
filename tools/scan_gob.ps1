param(
    [string]$ResDir = 'E:\Game\ps5\iso\[XBOX].Baldur''s.Gate.Dark.Alliance.[USA]\res'
)
$ErrorActionPreference = 'Stop'

function Parse-Container([byte[]]$b, [int]$nameSz, [int]$metaOff) {
    $count = [BitConverter]::ToInt32($b, 0)
    if ($count -lt 1 -or $count -gt 500) { return @() }
    $pos = 4
    $entries = @()
    for ($i = 0; $i -lt $count; $i++) {
        if ($pos + $nameSz + 8 -gt $b.Length) { break }
        $nb = New-Object System.Collections.Generic.List[byte]
        $nl = 0
        while ($nl -lt $nameSz -and $b[$pos + $nl] -ne 0) { [void]$nb.Add($b[$pos + $nl]); $nl++ }
        $nm = [System.Text.Encoding]::ASCII.GetString($nb.ToArray())
        $off = [BitConverter]::ToInt32($b, $pos + $metaOff)
        $sz  = [BitConverter]::ToInt32($b, $pos + $metaOff + 4)
        $pos += $nameSz + 8
        if ($off -ge 0 -and $off + $sz -le $b.Length -and $sz -gt 0) {
            $entries += [PSCustomObject]@{ Name = $nm; Off = $off; Size = $sz }
        }
    }
    return $entries
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

$allFiles = Get-ChildItem -LiteralPath $ResDir -Recurse -File
$report = @()
$containerParsed = 0
foreach ($f in $allFiles) {
    $ext = $f.Extension.ToLower()
    if ($ext -in @('.smg','.xmv','.m2v','.tex','.ico')) { continue }
    $b = [System.IO.File]::ReadAllBytes($f.FullName)
    if ($b.Length -lt 8) { continue }
    $entries = $null
    try {
        $entries = Parse-Container $b 56 56
        if ($entries.Count -eq 0) { $entries = Parse-Container $b 40 32 }
    } catch { $entries = $null }
    if ($entries -and $entries.Count -gt 0) {
        $containerParsed++
        foreach ($e in $entries) {
            if ($e.Size -gt 4194304) { continue }
            $data = New-Object byte[] $e.Size
            [Array]::Copy($b, $e.Off, $data, 0, $e.Size)
            $u16 = Get-U16Runs $data 15
            if ($u16.Count -gt 0) {
                $best = $u16 | Sort-Object Len -Descending | Select-Object -First 1
                $end = [Math]::Min($best.Pos + $best.Len * 2 - 1, $data.Length - 1)
                $s = [System.Text.Encoding]::Unicode.GetString($data[$best.Pos..$end])
                $report += [PSCustomObject]@{ Cntr = $f.Name; Sub = $e.Name; Size = $e.Size; MaxRun = $best.Len; Sample = $s.Substring(0, [Math]::Min(90, $s.Length)) }
            }
        }
    }
}
Write-Output "parsed containers: $containerParsed"
Write-Output "textual entries found: $($report.Count)"
$report | Sort-Object MaxRun -Descending | Select-Object -First 50 | Format-Table Cntr, Sub, Size, MaxRun, Sample -AutoSize -Wrap