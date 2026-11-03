$ErrorActionPreference = 'Stop'
$res = Get-Item -LiteralPath 'E:\Game\ps5\iso\[XBOX].Baldur''s.Gate.Dark.Alliance.[USA]\res'
$keywords = @('Nebbish','Elfsong','Branoch','Sleyvas','Kolgrim','Ciraxis','Xantam','Eldrith','Ilivarra','Alyth','Ethon','Osala','Keisen','Torrgeir')
$binary = New-Object System.Collections.Generic.List[byte]
foreach($k in $keywords){
    $ascii = [System.Text.Encoding]::ASCII.GetBytes($k)
    $utf16le = New-Object System.Collections.Generic.List[byte]
    foreach($ch in $ascii){ $utf16le.Add($ch); $utf16le.Add(0) }
    $f16 = $utf16le.ToArray()
    Write-Output "===== searching term: $k ====="
    foreach($f in (Get-ChildItem -LiteralPath $res.FullName -File -Recurse)){
        $fs = [System.IO.File]::Open($f.FullName, 'Open', 'Read', 'ReadWrite')
        try {
            $buf = New-Object byte[] ([Math]::Min(16MB, $fs.Length))
            $read = $fs.Read($buf, 0, $buf.Length)
            $chunk = New-Object byte[] $read
            [Array]::Copy($buf, $chunk, $read)
            $sAscii = [System.Text.Encoding]::ASCII.GetString($chunk)
            $sU16 = [System.Text.Encoding]::Unicode.GetString($chunk)
            if($sAscii.Contains($k) -or $sU16.Contains($k)){
                $posA = $sAscii.IndexOf($k)
                $posU = $sU16.IndexOf($k)
                Write-Output ("  {0} ({1:N0}B) ASCII@{2} U16@{3}" -f $f.Name, $f.Length, $posA, $posU)
            }
        } finally { $fs.Close() }
    }
}