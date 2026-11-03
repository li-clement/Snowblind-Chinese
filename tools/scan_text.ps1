param(
    [string]$ResDir = 'E:\Game\ps5\iso\[XBOX].Baldur''s.Gate.Dark.Alliance.[USA]\res',
    [string]$OutDir = 'E:\Game\ps5\iso\analysis\subfiles'
)
$ErrorActionPreference = 'Stop'
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

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

function Find-U16Runs([byte[]]$b) {
    $runs = @()
    $run = 0; $start = -1
    for ($i = 0; $i -lt $b.Length - 1; $i += 2) {
        $c = $b[$i]; $n = $b[$i + 1]
        if ($c -ge 0x20 -and $c -le 0x7E -and $n -eq 0) {
            if ($run -eq 0) { $start = $i }
            $run++
        } else {
            if ($run -ge 15) { $runs += [PSCustomObject]@{ Pos = $start; Len = $run } }
            $run = 0
        }
    }
    if ($run -ge 15) { $runs += [PSCustomObject]@{ Pos = $start; Len = $run } }
    return $runs
}

$lmpFiles = Get-ChildItem -LiteralPath $ResDir -Recurse -File -Filter '*.lmp'
$totalSub = 0
$report = @()
foreach ($lf in $lmpFiles) {
    $b = [System.IO.File]::ReadAllBytes($lf.FullName)
    if ($b.Length -lt 8) { continue }
    $entries = Parse-LmpEntries $b
    if ($entries.Count -eq 0) { continue }
    foreach ($e in $entries) {
        $totalSub++
        $ext = [IO.Path]::GetExtension($e.Name).ToLower()
        if ($ext -in @('.tex','.anm','.vif','.wav','.vag','.m2v','.xmv','.ico','.fnt','.smg','.vat','.va1')) { continue }
        $data = New-Object byte[] $e.Size
        [Array]::Copy($b, $e.Off, $data, 0, $e.Size)
        $runs = Find-U16Runs $data
        if ($runs.Count -gt 0) {
            $best = $runs | Sort-Object Len -Descending | Select-Object -First 1
            $end = [Math]::Min($best.Pos + $best.Len * 2 - 1, $data.Length - 1)
            $s = [System.Text.Encoding]::Unicode.GetString($data[$best.Pos..$end])
            $report += [PSCustomObject]@{ Parent = $lf.Name; Sub = $e.Name; Size = $e.Size; MaxRun = $best.Len; Sample = $s.Substring(0, [Math]::Min(80, $s.Length)) }
        }
        $safe = $lf.Name -replace '[\\/:*?"<>|]', '_'
        $dir = Join-Path $OutDir $safe
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
        [System.IO.File]::WriteAllBytes((Join-Path $dir $e.Name), $data)
    }
}
Write-Output "SUBFILES_TOTAL=$totalSub"
Write-Output "TEXTUAL=$($report.Count)"
$report | Sort-Object Parent, Sub | Format-Table Parent, Sub, Size, MaxRun, Sample -AutoSize -Wrap