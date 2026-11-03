$ErrorActionPreference = 'Stop'
$res = Get-Item -LiteralPath 'E:\Game\ps5\iso\[XBOX].Baldur''s.Gate.Dark.Alliance.[USA]\res'
$b = [System.IO.File]::ReadAllBytes((Join-Path $res.FullName 'tavern.gob'))
# find act1.uni / act1_ja.uni occurrences (filename + following fields) as seen at ~offset 5000
# From earlier dump @4584: "...act1_ja.uni..." pattern: 8-byte header then name... let's scan for both names
function Find-All([byte[]]$hay, [byte[]]$needle){
    $res2 = @()
    for($i=0; $i -lt $hay.Length - $needle.Length; $i++){
        $ok = $true
        for($j=0;$j -lt $needle.Length;$j++){ if($hay[$i+$j] -ne $needle[$j]){ $ok=$false; break } }
        if($ok){ $res2 += $i }
    }
    return $res2
}
foreach($nm in @('act1.uni','act1_ja.uni','act1_fr.uni')){
    $needle = [System.Text.Encoding]::ASCII.GetBytes($nm)
    $offs = Find-All $b $needle
    Write-Output "=== $nm found at: $($offs -join ', ') ==="
    foreach($o in $offs){
        # context: 16 bytes before and 48 after
        $s = [Math]::Max(0, $o - 16)
        $e = [Math]::Min($o + 48, $b.Length - 1)
        $ctx = $b[$s..$e]
        $hex = ($ctx | ForEach-Object { $_.ToString('X2') }) -join ' '
        Write-Output ("  @{0}: {1}" -f $o, $hex)
    }
}