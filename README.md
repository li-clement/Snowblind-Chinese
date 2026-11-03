# BGDA 汉化 —— Snowblind 引擎字体/文本补丁构建工程

Xbox《博德之门：黑暗联盟》(Baldur's Gate: Dark Alliance, USA) 的汉化构建工具链与全过程记录。
仓库里**只有我们自己产出的东西**：构建脚本、字体生成器、取证工具、译文库、分析笔记。

**当前基线：`v20 px16`** —— 中文字形 11px → **16px**，标题 / 主菜单 / 底部 Ⓐ 提示 / 对话全部逐帧验证通过。

## 目录

| 路径 | 说明 |
|---|---|
| `汉化可行性分析报告.md` | 最初的可行性分析：文本容器、字体格式、渲染入口 |
| `汉化进度.md` | 全过程记录（按轮次）。**第十九轮**是取证方法与结论的总复盘，含被撤回的错误结论 |
| `tools/build_v16b.py` | 字体生成器本体（11px 基线版），被后面的脚本 exec 复用其函数 |
| `tools/build_v17.py` | 去掉字号上限的版本（每个字体各自一张完整图集） |
| `tools/build_v18.py` | **主力构建脚本**：共享图集（薄头）+ 并集字表 + 重建 charmap，见下 |
| `tools/fontcap/` | 运行期取证工具（窗口级抓帧、XBE 反汇编辅助） |
| `translation/zh_*.uni.json` | 中文译文库，`{引擎字符串 key: 中文}` |
| `translation/jobs/zh_charset.txt` `zh_top1502.txt` `zh_punct.txt` | 字表：需要生成的汉字集合与标点 |

## 环境依赖

- Python 3.11 + `Pillow`（`numpy` 供取证脚本用）、`capstone`（`tools/fontcap/xr.py` 反汇编）
- 中文字体：`/System/Library/Fonts/Hiragino Sans GB.ttc`（字形渲染源，`build_v16b.py:16` 里可改）
- [extract-xiso](https://github.com/XboxDev/extract-xiso) 自编译二进制，路径 `extract-xiso-master/extract-xiso`
- 验证用：xemu 0.8.139（macOS）

## 需要准备但不入库的东西

本仓库刻意**不包含任何游戏文件**（ISO、解包树、原版资源、游戏截图、游戏原文全量导出）。
要跑通构建，需在工作目录下自行准备：

| 路径 | 内容 | 用途 |
|---|---|---|
| `[XBOX].Baldur's.Gate.Dark.Alliance.[USA]/res/` | extract-xiso 解包出来的游戏树 | 构建脚本就地替换 `res/font.lmp`、`res/frontend.lmp` 后回封 ISO |
| `backup_original/font.lmp`、`backup_original/frontend.lmp` | **未修改**的原版容器 | 字体生成的字形来源（拉丁/图标字形直接从原版 atlas 抠） |
| `extract-xiso-master/extract-xiso` | 自编译的打包工具 | `extract-xiso -c` 回封 ISO |
| `analysis/` | 中间产物 | 脚本自动创建（会把 `.fnt` 从原版容器里拆出来） |

## 构建

```bash
# v20 px16（当前基线）：中文 16px；gamefontsmall 保持完整字表，gamefontmed/creditfont 共享图集
python3 tools/build_v18.py \
  --thin gamefontmed.fnt,creditfont.fnt \
  --map gamefonta.fnt=16,gamefontmed.fnt=16,gamefontsmall.fnt=16,bigfont.fnt=16,creditfont.fnt=16 \
  --out bgda_zh_v20_px16.iso
```

`build_v18.py` 的其它开关：`--noshare`（每个字体各自完整图集，对照组）、`--keepjp`（保留原版日文字体）、
`--dry`（只算体积不写盘）。脚本会模拟引擎 `0x66890`/`0xC9280` 的指针换算并断言薄头与 master 的
`recptr`/`pixptr` 完全一致，装箱阶段就能挡住算错偏移的问题。

## 取证 / 验证

**不要用桌面截图的亮度判断"能不能开机"**——我这么错过一次，把黑屏版本判成了通过。可信做法只有一条：
按窗口 ID 抓 xemu 的画面（不依赖焦点、不受其它窗口遮挡），并且**轮询到主菜单再拍**（不同 ISO 载入耗时不同）。

```bash
python3 tools/fontcap/menu_shot.py bgda_zh_v20_px16.iso=analysis/menu.png
```

它做四件事：改写 xemu.toml 的 `dvd_path`（**只替换那一行，追加重复键会让 xemu 拒绝启动**）→ 启动 →
轮询"暗背景 + 四条菜单条"→ 抓帧 → 关模拟器。判据是主菜单底部 Ⓐ 圆环区的**峰值亮度**（阈值 75；
实测存在 87~95 / 缺失 29~50）。之所以用峰值而不是像素计数：这条提示会呼吸/闪烁，同一状态能读出 42~885。

## 几条用真金白银换来的规则

- **字体没有单文件大小上限**。黑屏的真因是「容器字节 + pow2 A8 纹理总量」把引擎 arena 打爆，
  撞进 `0xCAC90`/`0xC9310` 的无限重试。实测：容器+纹理 4.41MB ✅、5.27MB ✅、5.64MB ❌。
- **共享图集（薄头）只省容器字节，不省纹理**——每个 `.fnt` 条目仍各有位图头，引擎照旧各分配一张 pow2 纹理。
- **薄头只对 UTF-16 取字路径有效**。走 8 位 charmap 的文本（主菜单底部 "Ⓐ 确认"）在薄头上画不出来，
  所以 `gamefontsmall.fnt` 必须保留完整字表。
- **charmap 必须按自己的字表重建**，不能照抄原版：v14~v16 因为跳过 code `0x20` 让 8 位查表整体错位一格
  （`0x20→'!'`），中文走另一条路径所以长期没露馅。
- 字表要收录 **5 个原版字体的 code 并集**：`gamefontsmall` 独有的 `0x8C`（按键图标）漏了就画不出图标。

细节、证据表和逐条被撤回的结论都在 `汉化进度.md` 的第十七～十九轮。
