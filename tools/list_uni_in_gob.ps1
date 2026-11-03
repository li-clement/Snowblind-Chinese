$ErrorActionPreference = 'Stop'
$res = Get-Item -LiteralPath 'E:\Game\ps5\iso\[XBOX].Baldur''s.Gate.Dark.Alliance.[USA]\res'
$gobs = Get-ChildItem -LiteralPath $res.FullName -Recurse -File -Filter '*.gob'
$allUni = @()
foreach($g in $gobs){
    $b = [System.IO.File]::ReadAllBytes($g.FullName)
    # search for ".uni" filename patterns in the first 64KB (directory area) and whole file
    $ascii = [System.Text.Encoding]::ASCII.GetString($b)
    $matches = [regex]::Matches($ascii, '[a-z0-9_]{2,40}\.uni')
    $names = $matches.Value | Sort-Object -Unique
    if($names.Count -gt 0){
        foreach($n in $names){
            $allUni += [PSCustomObject]@{ GOB = $g.Name; Uni = $n }
        }
    }
}
Write-Output "=== 所有 .gob 内引用的 .uni 文件 ==="
$allUni | Sort-Object GOB, Uni | Format-Table -AutoSize
Write-Output ""
Write-Output "=== 去重统计 ==="
$allUni | Group-Object Uni | Sort-Object Name | Select-Object Name, Count | Format-Table -AutoSize