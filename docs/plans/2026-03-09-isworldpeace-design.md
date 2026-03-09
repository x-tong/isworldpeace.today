# Is World Peace Today — Design Document

## Overview

A minimalist static website that answers one question daily: "Is the world at peace today?" Data is sourced from Wikipedia's list of ongoing armed conflicts, updated automatically via GitHub Actions, and served via GitHub Pages.

## Goals

- 数据基本靠谱（来源 Wikipedia 武装冲突列表）
- 页面极简、截图友好、有传播性
- 零服务器成本（GitHub Pages + GitHub Actions）
- 数据结构预留扩展空间（历史曲线、地图等）

## Scope（第一版）

**包含：**
- 静态页面（YES/NO 展示）
- 数据管线（Python 抓取 Wikipedia）
- GitHub Actions 每日自动更新
- GitHub Pages 部署

**不包含（后续迭代）：**
- Twitter/X bot
- 冲突地图
- 历史曲线
- 和平概率指标

## Project Structure

```
isworldpeace.today/
├── index.html              # 单文件页面（含 CSS + JS）
├── status.json             # 数据文件（CI 自动更新）
├── update.py               # Wikipedia 冲突数据抓取
├── pyproject.toml           # Python 依赖（uv）
└── .github/
    └── workflows/
        └── update.yml      # 每天 UTC 0:00 运行
```

## Data Pipeline

### Source

Wikipedia: [List of ongoing armed conflicts](https://en.wikipedia.org/wiki/List_of_ongoing_armed_conflicts)

### Logic

1. 抓取页面 HTML
2. 解析所有 `wikitable` 表格
3. 按冲突强度分类统计（major wars / wars / minor conflicts / skirmishes）
4. 生成 `status.json`

### Output Format

```json
{
  "date": "2026-03-09",
  "peace": false,
  "conflicts": {
    "major_wars": 2,
    "wars": 5,
    "minor_conflicts": 12,
    "skirmishes": 8
  },
  "total": 27,
  "day_counter": 12873
}
```

- `day_counter`: 从 1945-09-02（二战结束日）到今天的天数
- `peace`: `total == 0` 时为 `true`

### Dependencies

- `requests`: HTTP 请求
- `beautifulsoup4`: HTML 解析

## Page Design

### Aesthetic: Editorial Brutalism

灵感：反战海报 + 报纸头版 + 纪念碑。

### Typography

- 标题 + "NO": **Playfair Display**（Google Fonts，衬线，力量感）
- 辅助文字: **DM Mono**（Google Fonts，等宽，数据感）

### Colors

| Element | Color | Note |
|---------|-------|------|
| 背景 | `#0a0a0a` | 接近纯黑 |
| "NO" | `#c23616` | 氧化铁红，带微弱 text-shadow |
| "YES"（备用） | `#27ae60` | 绿色 |
| 问题文字 | `#e0e0e0` | 浅灰白 |
| 辅助文字 | `#666` | 灰色 |
| 底部铭文 | `#444` | 暗灰 |

### Layout

垂直居中，全屏视口。从上到下：

1. "Is the world at peace today?" — 大号衬线体
2. "NO" — 占视口约 40% 高度，氧化铁红
3. "Day 12,873 of asking." — 等宽字体，灰色
4. "27 active conflicts · 2026-03-09" — 更小更灰
5. 分隔线
6. "If this page ever shows YES, humanity achieved something remarkable." — 暗灰铭文

### Animation

- "NO" 加载时 `opacity: 0 → 1` + `scale(1.02 → 1)`，缓慢淡入（~1s）
- 底部铭文延迟 1s 淡入
- 无花哨动效，克制即力量

### Texture

- CSS grain effect（极淡 noise overlay），模拟旧纸张/混凝土质感

### Responsive

- `clamp()` 控制字号，手机上 "NO" 仍然震撼
- 间距自适应，信息密度不变

### Social Sharing

- `og:title`: "Is the world at peace today?"
- `og:description`: "NO. Day 12,873 of asking. 27 active conflicts."
- 动态生成 description 内容

## CI/CD

### GitHub Actions (`update.yml`)

- 触发：`cron: "0 0 * * *"`（每天 UTC 0:00）+ 手动触发
- 步骤：
  1. checkout
  2. 安装 Python + 依赖
  3. 运行 `update.py`
  4. commit + push `status.json`

### GitHub Pages

- 从 `main` 分支根目录部署
- `status.json` 更新后自动生效

## Future Iterations

预留扩展方向（不在第一版范围内）：

1. **历史曲线**：git history 中积累 `status.json` 数据，用 Chart.js 展示
2. **冲突地图**：需要额外地理位置数据源
3. **和平概率指标**：基于趋势的简单计算或 meme 式 "0%"
4. **Twitter/X bot**：每日自动发推
