# prep_translation_jobs.ps1 (ASCII only) - split translation jobs and write term glossary
$ErrorActionPreference = 'Stop'
$csv = Import-Csv 'E:\Game\ps5\iso\translation\translation_en.csv'
$jobDir = 'E:\Game\ps5\iso\translation\jobs'
New-Item -ItemType Directory -Force -Path $jobDir | Out-Null

$files = $csv | Group-Object File | Sort-Object Count -Descending
foreach($grp in $files){
    $rows = $grp.Group
    $sb = New-Object System.Text.StringBuilder
    [void]$sb.AppendLine("FILE=$($grp.Name)")
    [void]$sb.AppendLine("ENTRIES=$($rows.Count)")
    [void]$sb.AppendLine("-----")
    foreach($r in $rows){
        $e = $r.En -replace "`r`n", ' / ' -replace "`n", ' / '
        [void]$sb.AppendLine("[$($r.Key)]")
        [void]$sb.AppendLine($e)
    }
    $safe = $grp.Name -replace '[^a-zA-Z0-9_.-]', '_'
    Set-Content -LiteralPath (Join-Path $jobDir "en_$safe.txt") -Value $sb.ToString() -Encoding UTF8
    Write-Output ("job: en_$safe.txt  ($($rows.Count) entries)")
}

# term glossary
$terms = @'
统一术语表(简体中文 D&D 常用译名,翻译时必须遵守):
[角色/人名]
Alyth = 阿丽丝; Nebbish = 内比什; Ethon = 埃松; Xantam = 赞塔姆; Ciraxis = 西拉西斯
Eldrith = 艾尔德瑞斯; Sess'sth = 塞斯斯; Ilivarra = 伊莉瓦拉; Kolgrim = 科尔格里姆
Torrgeir = 托尔盖尔; Brogan = 布罗根; Keissen/Keisen = 凯森; Osala = 奥萨拉
Ipswitch = 伊普斯维奇; Drizzt = 崔斯特; Keledon = 凯勒顿; Sleyvas = 斯莱瓦斯
Garik = 加里克; Fayed = 费德; Hoochie = 胡奇; Branoch = 布拉诺克; Bartley = 巴特利
Karne = 卡恩; Chelimber = 切林伯尔; Dumathoin = 杜玛松; Sahri = 萨赫里
Clangeddin = 克兰格丁; Otiluke = 欧提路克; Mordenkainen = 摩登凯恩
Drizzt 双刀: Icingdeath = 冰亡(霜寒弯刀), Twinkle = 闪光(防御弯刀)

[地名/组织]
Elfsong Tavern = 精灵之歌酒馆; Onyx Tower = 黑曜石之塔; Burning Eye = 燃烧之眼
Adderspine Road = 蛇脊大道; The Marsh = 大沼泽; Rotting Bog = 腐烂泥沼
Sinking Temple = 沉没神殿; Sunken Chapel = 沉没礼拜堂; Hall of Remembrance = 追忆大厅
Eldrith's Watch = 艾尔德瑞斯之望; Black Forge = 黑熔炉; Water Stair = 水之阶梯
Mining Camp = 采矿营地; Drow Underworld = 卓尔地下世界; Snow Cave = 雪之洞窟
Ice Cave = 冰之洞窟; Ciraxis' Lair = 西拉西斯之巢; Wind's Walk = 风之行者
Thieves' Guild = 盗贼公会; Realm of the Dead / Undead = 亡灵; The Gauntlet = 试炼场
Chelimber's Crown = 切林伯尔之冠; Chelimber's Keep = 切林伯尔要塞

[种族/职业/系统词]
Drow = 卓尔; Elf = 精灵; Dwarf = 矮人; Human = 人类; Half-Orc = 半兽人
Sorceress = 术士; Fighter = 战士; Ranger = 游侠; Arcane Archer = 奥术射手
Health = 生命; Energy = 能量; Mana = 法力; Armor = 护甲; Damage = 伤害
Experience = 经验; Level = 等级; Quest = 任务; Inventory = 背包
Feat = 专长; Skill = 技能; Spell = 法术; Potion = 药水; Scroll = 卷轴
Save Game = 存档; Load = 读取; Memory Unit = 记忆卡; Hard Disk = 硬盘
Extreme Mode = 极限模式; Stat = 属性; Constitution = 体质; Charisma = 魅力
Wisdom = 感知; Intelligence = 智力; Dexterity = 敏捷; Strength = 力量
Will Saving Throw = 意志豁免; Reflex Saving Throw = 反射豁免; Fortitude Saving Throw = 强韧豁免
Armor Class = 护甲等级; Hit Points = 生命值; Damage/second = 每秒伤害
Recall Potion = 传送药水; Rejuvenation = 活力(法药); Healing = 治疗(血药)

[格式符规则]
1. 保留全部 %d %c %f %s %c 等格式符,位置可调整到中文语序合适处
2. 保留 {} 与 ~ 符号(它们是按钮图标占位符)
3. / 表示多行文本(如奖励列表),翻译时保留 / 作为换行分隔
4. %c 后常跟英文按钮名(P1/P2/Equip/Back 等),按钮名也翻译成中文,但 %c 本身保留
'@
Set-Content -LiteralPath (Join-Path $jobDir '_term_glossary.txt') -Value $terms -Encoding UTF8
Write-Output "glossary written"