# 和弦进行建议器 Web 版 · Phase 1 §6 第 2 项

> **状态**:v0 目录骨架(2026-09-15 T5 落地)
> **任务**:`项目开发计划.md` §6 第 2 项「和弦进行建议器 Web 版:输入调性 + 情绪,返回 5-8 候选 + 试听」
> **关联**:
> - [项目开发计划.md](../../项目开发计划.md) §6 第 2 项
> - [9/15 T1 巡检报告](../../.Log/巡检-音乐-20260915.md) P0 #1
> - [9/14 §6 第 1 项乐理问答飞书机器人](../feishu_bot/) — 同 Phase 1 起步期 + 同 Tone.js 大版本

---

## 产品定位

Web 端(Web 主入口,飞书 Agent 辅),输入**调性 + 情绪** → 返回 **5-8 候选和弦进行** + **Tone.js 试听**,定位 3 类用户:

- **业余/进阶器乐学习者**:问"想写一首忧伤的小调" → 5 候选小调进行 + 每条试听
- **独立音乐人 / 词曲创作者**:写副歌卡壳 → 输入"史诗 + Am" → 同名小调化史诗进行 + 试听比较
- **制作人 / 编曲师**:编曲 demo → 试 5 种进行 + 替换其中 1 个和弦 → 实时试听

区别于 §6 第 1 项乐理问答(纯乐理知识问答):本项是**生成式 + 试听式**建议,需 Tone.js 真出声。

## 架构

```
app/chord_suggester/
├── README.md                 # 本文件
├── __init__.py               # 包导出(纯 Python,无需 Node.js)
├── package.json              # Next.js 14 + Tone.js 14.7.77 锁版本
├── chord_progressions.py     # 12 经典进行模板 + 候选算法(186 行)
├── emotion_keyword.py        # 8 档情绪映射 + EmotionMapper(131 行)
├── key_normalize.py          # 24 调归一 + KeyNormalizer(170 行)
├── audio_playback.py         # Tone.js 试听函数 JS 源码(77 行)
├── page.template.tsx         # Next.js 14 主页面契约(v0 骨架)
├── api_suggest.template.ts   # Next.js API 路由契约(v0 骨架)
└── tests/
    ├── __init__.py
    └── test_chord_suggester.py  # 17 用例覆盖(v0 全绿)
```

总 **10 文件 / 809 行(含 README.md 113 行则 ~922 行)**,与 9/14 §6 第 1 项"10 文件 534 行"同规模。

## 算法

### 输入

- **调性** `key`: 24 选 1,12 大调(C/D/E/F/G/A/B + 5 个 #) + 12 小调(Am/Dm/Em/Fm/Gm/Bm + 5 个 #m)
- **情绪** `emotion`: 8 档 — happy/sad/tense/calm/epic/tender/mysterious/jazzy
- **候选数** `n`: 5-8,默认 6

### 候选生成

`PROGRESSIONS_LIBRARY` 12 条经典进行 + 各自 8 档情绪权重(0-1):

| id | name | roman_major | roman_minor | 主调 |
|----|------|-------------|-------------|------|
| I-V-vi-IV | Pop Anthem | I-V-vi-IV | i-V-VI-iv | happy/epic/tender |
| vi-IV-I-V | Emotional Ballad | vi-IV-I-V | i-iv-VII-V | sad/tender |
| ii-V-I | Jazz Turnaround | ii-V-I | ii°-V-i | jazzy/calm |
| I-vi-IV-V | 50s Doo-wop | I-vi-IV-V | i-VI-iv-V | happy/calm |
| I-IV-V-I | Folk Classic | I-IV-V-I | i-iv-V-i | calm/tender |
| I-bVII-IV-I | Mixolydian Vibe | I-bVII-IV-I | i-bVII-iv-i | epic/mysterious |
| vi-IV-I-V | Andalusian | vi-IV-I-V | i-VII-VI-V | sad/mysterious |
| i-iv-V-i | Natural Minor | i-iv-V-i | i-iv-V-i | sad(权重 1.0) |
| i-bVI-bIII-bVII | Epic Progression | i-bVI-bIII-bVII | i-bVI-bIII-bVII | epic(权重 1.0) |
| 12-bar Blues | 12-bar Blues | I-I-I-I-IV-IV-I-I-V-IV-I-V | 同结构 | jazzy/sad |
| I-bIII-IV-bVI | Doo-wop Descend | I-bIII-IV-bVI | i-bIII-iv-bVI | sad/tender |
| I-V-vi-iii-IV | Descending Circle | I-V-vi-iii-IV-I-IV-V | i-V-VI-iv-i-V-iv-V | calm/epic |

排序:每个进行按 `emotion_tags[emotion]` 加权排序,取前 n。

输出:每条候选含 `id / name / roman / description / emotion_score / key / is_minor`。

### 情绪映射

8 档情绪 × 中英文关键词 × 24-30 关键词/档:

- `happy`: 快乐/欢快/明亮/阳光/happy/joyful/cheerful/bright/... (BPM 100-140)
- `sad`: 忧伤/忧郁/深沉/sad/melancholy/sorrow/gloomy/... (BPM 60-90)
- `tense`: 紧张/悬疑/压迫/tense/anxious/suspenseful/... (BPM 110-150)
- `calm`: 平静/安宁/禅意/calm/peaceful/serene/meditative/... (BPM 60-80)
- `epic`: 史诗/壮阔/震撼/epic/grand/heroic/cinematic/... (BPM 90-120)
- `tender`: 温柔/柔情/缠绵/tender/gentle/sweet/warm/... (BPM 70-100)
- `mysterious`: 神秘/玄妙/空灵/mysterious/ethereal/dreamy/... (BPM 80-110)
- `jazzy`: 爵士/摇摆/拉丁/jazzy/swing/bossa/latin/... (BPM 90-130)

EmotionMapper 支持中英文自由文本匹配,v0 直接命中,v1 加 LLM 兜底。

### 调性归一

`KeyNormalizer.normalize(raw)` 输入支持 6 种变体:

- `"C"` / `"Am"` — 简洁
- `"C major"` / `"A minor"` — 英文后缀
- `"C大调"` / `"A小调"` — 中文后缀
- `"Db major"` / `"Bb"` — 等音(flat 自动转 sharp,Db→C#/Bb→A#)
- `"f# minor"` — 大小写不敏感
- `""` / `"H"` — 抛 ValueError

`KeyNormalizer.relative_key(canonical)` 关系调互换(C↔Am/G↔Em)。

### 试听(Tone.js)

`audio_playback.py` 内置 70+ 行 Tone.js 14.7.77 JS 源码,导出 `playProgression(romanArray, root, bpm)`:

- 动态 import Tone.js CDN(避免 SSR 报错)
- PolySynth 三角波 + 0.02s attack + 0.5s release
- 7 个罗马数字级别(I/II/III/IV/V/VI/VII)+ 6 个变化(bVII/bVI/bIII/小写 i/ii/v/vi/vii)
- 自动 baseOctave=4,逐和弦间隔 `(60/bpm)*1000ms`

Phase 1 v1(9/16 ~ 9/20)真跑,npm install tone@14.7.77 后可立即用。

## 与其他模块的关系

- **§6 第 1 项乐理问答飞书机器人**(`app/feishu_bot/`):同 Tone.js 14.7.77,音色/扩展音互通;互补(问答 vs 生成建议)
- **§6 第 4 项 MIDI 素材库最小版**:本建议器的"试听"用 Tone.js 合成,§6 第 4 项的"试听"用真实 MIDI 回放 — 两条路径最终汇合到"风格灵感试听"
- **任务 9 LLM 乐理问答基线评估**(`analysis_demo/llm_eval/`):EmotionMapper v1 可接 LLM 兜底(关键词无命中时让 LLM 推断情绪)
- **任务 8 MIDI 标签体系骨架**(`analysis_demo/scores/midi_tags_v0.json`):8 类情绪 × 16 一级风格 与本建议器情绪映射口径一致,可作为标签筛选上游

## v0 落地清单(本期)

- [x] 目录骨架 `app/chord_suggester/`(10 文件 809 行 + README)
- [x] 12 经典和弦进行模板(每条带 8 档情绪权重)
- [x] `suggest_progressions(key, emotion, n)` 算法(支持 5-8 候选,大小调区分)
- [x] 8 档情绪 × 中英文关键词映射(`EmotionMapper`)
- [x] 24 调归一 + 等音(flat→sharp)+ 关系调互换(`KeyNormalizer`)
- [x] Tone.js 试听函数 JS 源码(7 个罗马数字 + 6 个变化级别)
- [x] Next.js 14 主页面契约 `page.template.tsx`(调性+情绪+数量+候选+试听按钮)
- [x] Next.js API 路由契约 `api_suggest.template.ts`(POST /api/suggest)
- [x] `package.json` 锁 Next 14.2 + React 18.3 + Tone 14.7.77
- [x] 17 单元测试 100% 通过(候选算法 + 情绪匹配 + 调性归一 + JS 完整性)

## Phase 1 续做清单

- [ ] **v1 · 9/16 ~ 9/20**: `npx create-next-app@14` 真跑 + Tone.js 真出声 + 试听按钮真触
- [ ] **v1 · 9/16 ~ 9/20**: 候选数扩 30+ 经典进行(Blues 9 / 爵士 12 / 民谣 5 / 流行 5 / 影视 4)
- [ ] **v2 · 9/21 ~ 9/27**: 用户自定义和弦 + 单和弦替换功能(选中候选中某个和弦 → 弹出替换面板)
- [ ] **v2 · 9/21 ~ 9/27**: EmoLLM 兜底(关键词未命中 → LLM 推断情绪档位 + 置信度)
- [ ] **v2 · 9/21 ~ 9/27**: 候选标记"AI 建议,非乐谱" + 人工修正按钮(对应 §8 风险与下一步)
- [ ] **v3 · 9/28 ~ 9/30**: 试听保存为 MIDI 文件 + 一键导回 §6 第 4 项 MIDI 素材库

## 测试

```bash
cd /Users/aaron/Mac/Consultant/19-音乐-Music/_MusicLib/MusicWeb
python3 -m app.chord_suggester.tests.test_chord_suggester
# 17 passed, 0 failed, 17 total
```

无需 Node.js / npm install,纯 Python 测试覆盖所有 v0 算法契约。

## 不做什么

- **不做**真实 LLM 调用(留 v1 / v2)
- **不做**Next.js 项目真实启动(`npx create-next-app` 留 v1)
- **不做**真实音色采样(Salamander Grand Piano 留 v1 评估 CDN 加载速度)
- **不做**候选保存为图片(留 v2,可截图功能)
- **不做**用户认证 / 收藏 / 分享(v2 后再说,Phase 1 MVP 不需要)

## 历史

- **2026-09-15** · v0 目录骨架落地(本份),10 文件 809 行 + 17 测试 100%,Phase 1 §6 第 2 项 1 commit 启动