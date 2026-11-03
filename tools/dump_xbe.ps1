$ErrorActionPreference = 'Stop'
$root = 'E:\Game\ps5\iso\[XBOX].Baldur''s.Gate.Dark.Alliance.[USA]'
$b = [System.IO.File]::ReadAllBytes((Join-Path $root 'default.xbe'))
Write-Output "XBE size: $($b.Length)"
# extract ascii strings >= 6
$strs = New-Object System.Collections.Generic.List[string]
$cur = New-Object System.Text.StringBuilder
for($i=0; $i -lt $b.Length; $i++){
    $c = $b[$i]
    if($c -ge 32 -and $c -le 126){
        [void]$cur.Append([char]$c)
    } else {
        if($cur.Length -ge 6){ $strs.Add($cur.ToString()) }
        [void]$cur.Clear()
    }
}
if($cur.Length -ge 6){ $strs.Add($cur.ToString()) }
Write-Output "XBE ascii strings >=6: $($strs.Count)"
# search for text-related strings
Write-Output "=== strings matching: gtext/uni/font/lmp/ja/dialog/text/lang ==="
$strs | Where-Object { $_ -match 'gtext|\.uni|font|\.lmp|dialog|lang|text|jap' } | Select-Object -Unique | Select-Object -First 80
Write-Output ""
Write-Output "=== strings containing typical dialogue words ==="
$strs | Where-Object { $_ -match 'Elfsong|Nebbish|goblin|Alyth|Vahn|Kromlech|Adrianna|sword|shield|tavern' } | Select-Object -First 40