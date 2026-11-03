# split_gtext.ps1 (ASCII only) - split en_gtext.uni.txt into 2 halves by [key] blocks
$ErrorActionPreference = 'Stop'
$jobDir = 'E:\Game\ps5\iso\translation\jobs'
$src = Join-Path $jobDir 'en_gtext.uni.txt'
$lines = Get-Content -LiteralPath $src -Encoding UTF8
# header: lines 1-3 (FILE/ENTRIES/-----), rest are [key]\nEnglish\n\n blocks
$header = $lines[0..2]
$body = $lines[3..($lines.Count-1)]
# find block start indices
$blocks = New-Object System.Collections.Generic.List[object]
$cur = -1
for($i=0;$i -lt $body.Count;$i++){
    if($body[$i] -match '^\['){ if($cur -ge 0){ $blocks.Add([PSCustomObject]@{ Start=$cur; End=$i-1 }) }; $cur = $i }
}
if($cur -ge 0){ $blocks.Add([PSCustomObject]@{ Start=$cur; End=$body.Count-1 }) }
Write-Output "gtext blocks: $($blocks.Count)"
$half = [Math]::Ceiling($blocks.Count / 2)
Write-Output "split at block $half"

$p1 = New-Object System.Collections.Generic.List[string]
$p1.Add('FILE=gtext_part1.uni')
$p1.Add("ENTRIES=$half")
$p1.Add('-----')
for($i=0;$i -lt $half;$i++){ for($j=$blocks[$i].Start;$j -le $blocks[$i].End;$j++){ $p1.Add($body[$j]) } }
Set-Content -LiteralPath (Join-Path $jobDir 'en_gtext_part1.uni.txt') -Value $p1 -Encoding UTF8

$p2 = New-Object System.Collections.Generic.List[string]
$p2.Add('FILE=gtext_part2.uni')
$p2.Add("ENTRIES=$($blocks.Count - $half)")
$p2.Add('-----')
for($i=$half;$i -lt $blocks.Count;$i++){ for($j=$blocks[$i].Start;$j -le $blocks[$i].End;$j++){ $p2.Add($body[$j]) } }
Set-Content -LiteralPath (Join-Path $jobDir 'en_gtext_part2.uni.txt') -Value $p2 -Encoding UTF8
Write-Output "written part1 ($half) and part2 ($($blocks.Count - $half))"