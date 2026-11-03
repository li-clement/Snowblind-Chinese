$ErrorActionPreference = 'Stop'
$files = @(
    @{Path='E:\Game\ps5\iso\analysis\japfontbig0.fnt'; Tag='japfontbig0'},
    @{Path='E:\Game\ps5\iso\analysis\gamefonta.fnt'; Tag='gamefonta'},
    @{Path='E:\Game\ps5\iso\analysis\bigfont.fnt'; Tag='bigfont'},
    @{Path='E:\Game\ps5\iso\analysis\japfontsmall0.fnt'; Tag='japfontsmall0'}
)
foreach($item in $files){
    $p = $item.Path; if(-not (Test-Path $p)){ continue }
    $b = [System.IO.File]::ReadAllBytes($p)
    Write-Output "========== $($item.Tag) (size $($b.Length)) =========="
    $u16_0 = [BitConverter]::ToUInt16($b,0)
    $u16_2 = [BitConverter]::ToUInt16($b,2)
    $u32_4 = [BitConverter]::ToUInt32($b,4)
    $u32_8 = [BitConverter]::ToUInt32($b,8)
    $u32_12 = [BitConverter]::ToUInt32($b,12)
    $u32_16 = [BitConverter]::ToUInt32($b,16)
    Write-Output ("hdr: u16[0]={0} u16[2]={1} u32[4]={2} u32[8]={3} u32[12]=0x{4:X} u32[16]=0x{5:X}" -f $u16_0,$u16_2,$u32_4,$u32_8,$u32_12,$u32_16)
    # 0x100 处字符映射表: 每项 4 字节 (charCode u16, index u16)? 数一数非 FF 的对
    $pairs = @()
    for($o = 0x100; $o + 3 -lt $b.Length; $o += 4){
        $c = [BitConverter]::ToUInt16($b, $o)
        $idx = [BitConverter]::ToUInt16($b, $o+2)
        if($c -eq 0xFFFF -and $idx -eq 0xFFFF){ continue }
        $pairs += [PSCustomObject]@{Ch=$c; Idx=$idx; Off=$o}
        if($pairs.Count -ge 20){ break }
    }
    Write-Output "char->idx table start @0x100, first entries:"
    $pairs | Select-Object -First 12 | ForEach-Object { Write-Output ("  U+{0:X4} -> glyph {1}" -f $_.Ch, $_.Idx) }
    # 统计整个表的有效条目数(非 FFFF)
    $valid = 0
    for($o = 0x100; $o + 3 -lt $b.Length; $o += 4){
        $c = [BitConverter]::ToUInt16($b, $o)
        if($c -ne 0xFFFF){ $valid++ }
    }
    Write-Output "total valid entries in table from 0x100: $valid"
    Write-Output ""
}