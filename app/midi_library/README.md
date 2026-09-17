# MIDI 素材库最小版 · Phase 1 §6 第 4 项

> **状态**:v0 目录骨架(2026-09-17 T5 落地) + 续做批量入库脚手架 v0(2026-09-18 T5 落地)
> **任务**:`项目开发计划.md` §6 第 4 项「MIDI 素材库最小版:1 万条种子素材,支持 BPM/调性/情绪筛选」
> **关联**:
> - [项目开发计划.md](../../项目开发计划.md) §6 第 4 项 + §5 第 88 项脚手架部分
> - [9/17 T1 巡检报告](../../.Log/巡检-音乐-20260917.md) P0 #1(救火 + 守卫 + §6 第 4 项三效合一第 4 周期)
> - [9/18 T5 续做报告](../../.Log/巡检-音乐-20260918.md) P0 命中(本日 commit 内)
> - [分析 demo midi_tags_v0 标签体系](../../analysis_demo/scores/midi_tags_v0.json) — 4 维标签字典 16 一级风格 + 8 类情绪 + 5 档 BPM + 24 调性 + 5 示例
> - [9/16 §6 第 3 项音频分析 MVP](../audio_analysis/) — 同 Phase 1 起步期,感知式(音频 → 结构化乐理信息)
> - [9/15 §6 第 2 项和弦进行建议器](../chord_suggester/) — 同 Phase 1 起步期,生成式(情绪 + 调性 → 候选和弦进行)
> - [9/14 §6 第 1 项乐理问答飞书机器人](../feishu_bot/) — 同 Phase 1 起步期,纯文字问答

---

## 产品定位

**核心场景**:用户在音乐人/创作者侧 → 输入「我想要一首忧郁的慢板流行,MIDI 风格拆解参考」→ 返回 **5-8 套 MIDI 动机/和弦走向/鼓组律动模板** → 试听 + 替换 + 一键拖入 DAW → 释放创作灵感。

**目标用户**(沿用 §1 三群):

- **业余/进阶器乐学习者**:"我想学一首 R&B 风格的歌" → 输入风格 + BPM → 拿到经典 ii-V-I 链条的 MIDI → 在 Tone.js 试听 + 自己尝试
- **独立音乐人 / 词曲创作者**:写新歌卡壳 → 输入调性 + 情绪 → 拿到「同调性 + 同情绪 + 经典走向」骨架 → 加自己的旋律动机
- **制作人 / 编曲师**:做项目需要快速找 reference → 输入 BPM + 调性 → 一键试听 5 套模板 → 选最接近情绪的继续做

**区别于 §6 第 1 + 2 + 3 项**:

- §6 第 1 项乐理问答:**纯文字问答**(乐理知识)
- §6 第 2 项和弦建议:**生成式**(情绪 + 调性 → 候选和弦进行,**不绑死 MIDI**)
- §6 第 3 项音频分析:**感知式**(用户上传音频 → 结构化乐理信息)
- **§6 第 4 项(本项)MIDI 素材库**:**检索式**(MIDI 元数据 → 候选 MIDI,内置 5 起步 → 1 万目标)

## 架构

```
app/midi_library/
├── README.md                  # 本文件(设计文档)
├── __init__.py                # 包导出 5 + 7 主体(823 + batch_loader 7)
├── index_meta.json            # M-001~M-010 索引元数据(沿用 midi_tags_v0 schema)
├── midi_loader.py             # MIDI 文件加载 + metadata 提取(95 行)
├── tag_filter.py              # 按 BPM/调性/情绪/风格 4 维筛选(80 行)
├── progression_builder.py     # MIDI 音符 → 和弦进行提取(85 行)
├── search_engine.py           # 标签 + 自由文本混合检索(75 行)
├── pipeline.py                # 端到端 query → 候选 MIDI 编排(110 行)
├── batch_loader.py            # 批量入库脚手架 v0(2026-09-18 续做,~270 行)
├── api_search.template.ts     # Next.js 14 GET /api/midi/search 路由契约(90 行)
├── requirements.txt           # mido/pretty_midi/numpy 锁版本
└── tests/
    ├── __init__.py
    └── test_midi_library.py   # 45 用例 100% 通过(31 + 14 batch_loader)
```

**总 12 文件 / ~9 KB README + ~790 行 Python + ~90 行 TS + ~430 行测试 ~ 1 万行目标(Phase 1 续做)**,与 9/14 + 9/15 + 9/16 + 9/17 §6 第 1/2/3/4 项同模式同规模。

## 模块接口契约

### 输入

- **MIDI 元数据查询**:BPM 范围 / 调性 KY-XX / 情绪 MO-XX / 风格 ST-XX / 自由文本关键词
- **最大返回**:≤ 20 条候选(可在 api_search.template.ts 调整)
- **MIDI 文件**:Phase 1 续做时通过 mido/pretty_midi 加载,本骨架仅 metadata 链 + 元数据索引

### 输出(MIDILibraryResult JSON)

```json
{
  "query": {
    "bpm_range": [70, 130],
    "key_codes": ["KY-13", "KY-14"],
    "mood_codes": ["MO-02", "MO-06"],
    "style_codes": ["ST-01"],
    "free_text": "抒情钢琴"
  },
  "matched": [
    {
      "id": "M-001",
      "title": "Pop Ballad Sketch",
      "style_primary": "ST-01 流行",
      "mood": ["MO-02 忧郁", "MO-06 亲密"],
      "tempo": "TP-02 中速",
      "bpm": 72,
      "key": "KY-14 d minor",
      "duration_sec": 240,
      "tags": ["抒情", "钢琴 + 弦乐", "慢板", "情歌"],
      "match_score": 0.95,
      "matched_fields": ["mood", "style", "tempo"]
    }
  ],
  "total": 1,
  "meta": {
    "version": "0.1.0",
    "phase": "Phase 1 §6 第 4 项 v0 目录骨架",
    "elapsed_ms": 12
  }
}
```

## 标签字典契约(沿用 midi_tags_v0)

| 维度 | ID 命名 | 总数 | 示例 |
|---|---|---|---|
| 风格 | ST-XX | 16 | ST-01 流行 / ST-03 爵士 / ST-04 电子 / ST-07 古典 / ST-15 民乐 |
| 情绪 | MO-XX | 8 | MO-02 忧郁 / MO-04 放松 / MO-06 亲密 / MO-08 激励 |
| BPM | TP-XX | 5 | TP-01 慢板 < 70 / TP-02 中速 70-100 / TP-04 快板 130-170 |
| 调性 | KY-XX | 24 | KY-13 F major / KY-14 d minor / KY-20 f minor |

## 批量入库脚手架契约(2026-09-18 续做 v0)

> **目的**:Phase 1 续做 100 → 1000 → 1 万 MIDI 入库时,提供 CLI 级工具,避免逐条手工改 `index_meta.json`。

**模块**:`app/midi_library/batch_loader.py`(270 行,7 主体导出)

| 主体 | 类型 | 作用 |
|---|---|---|
| `BatchValidationError` | dataclass | 单条错误(line_no / id / field / reason) |
| `BatchValidationReport` | dataclass | 批校验聚合报告(total / passed / failed / errors)+ `is_all_pass()` + `to_dict()` |
| `validate_entry(entry, existing_ids)` | 函数 | 单条 schema 校验,返回错误列表 |
| `validate_batch(entries, existing_ids)` | 函数 | 批校验,聚合所有错误并标记行号 + batch 内查重 |
| `next_id(prefix, existing_ids)` | 函数 | 自动生成下一个 ID(如 `M-011`) |
| `append_batch(entries, index_path, *, batch_id, dry_run=True)` | 函数 | 追加批次到 index_meta.json,自动更新 `_meta.last_batch_id/at/size/total_entries/last_batch_coverage` |
| `load_batch_json(path)` | 函数 | 读 JSON 文件(支持顶层数组或 `{entries:[...]}`) |

**校验规则**(10 项,覆盖 4 维标签 + 字段完整性):

1. `id` 格式 `M-XXX`(M + 横线 + 3+ 位数字)+ 不与 `existing_ids` 重复
2. `title` 非空
3. `style_primary` 必须以 `ST-01` ~ `ST-16` 开头
4. `mood[]` 每项必须以 `MO-01` ~ `MO-08` 开头
5. `tempo` 必须以 `TP-01` ~ `TP-05` 开头
6. `key` 必须以 `KY-01` ~ `KY-24` 开头
7. `bpm` 整数,1 ≤ bpm ≤ 300
8. `duration_sec` 整数,≥ 1
9. `tag_count_total` 与 `len(tags)` 必须相等
10. `style_subtag` / `scale` / `time_signature` 非空

**CLI 用法**:

```bash
# 默认 dry_run,仅校验不写
python -m app.midi_library.batch_loader --input batch_100.json

# 加 --commit 真写
python -m app.midi_library.batch_loader --input batch_100.json --commit \
    --batch-id "2026-09-23-batch-01"

# 输出示例(DRY_RUN 失败)
[DRY_RUN] total=100 passed=98 failed=2
[ERRORS]
  line=12 id='M-022' field=mood[1] reason=mood[1] 不在 MO-01 ~ MO-08 范围,实际: 'MO-99 想象'
  line=47 id='M-057' field=bpm reason=bpm 超出 1 ~ 300 范围,实际: 500
```

**写入行为**:

- **校验失败** → 立即返回 `BatchValidationReport`,**不写文件**(原子性)
- **dry_run=True** → 即使校验通过也不写
- **dry_run=False** → 真写 index_meta.json,自动追加 `_meta.last_batch_id/at/size/total_entries/last_batch_coverage`(覆盖度统计 style_count / mood_count / tempo_count / key_count)

## 与其他模块的协作

- **§6 第 2 项 chord_suggester**(T5 9/15):本库返回 MIDI 候选后,`chord_suggester` 可对每个 MIDI 跑「和弦进行提取」拿到 4-8 个和弦进行 → 返回给用户试听
- **§6 第 3 项 audio_analysis**(T5 9/16):用户上传参考曲 → 拿到调性 + BPM → 直接 query 本库「同调性 + 同 BPM」→ 5 套参考 MIDI
- **§5 任务 8 MIDI 标签体系骨架 v0**(`midi_tags_v0.json`,T5 9/11):本库延续其 schema 4 维 + 5 示例,索引元数据直接挂在 `_addendum.phase_1_targets` 之后
- **InspirationIndex.md §四**:Phase 1 续做时补登记 MIDI 标签字典 1 行 + 库目录登记 1 行

## Phase 1 续做路线图

- **9/17 ~ 9/22** · M-001 ~ M-010(本批次 5 + 新 5)= 10 条 schema 锚点(v0 完成)
- **9/18** · `batch_loader.py` 批量入库脚手架 v0 落地(本日 commit,CLI + 14 测试 100% 通过)
- **9/23 ~ 9/27** · M-011 ~ M-110(批次 11 × 10 = 100 条,用 `batch_loader.py --commit` 入库,每 10 条 1 commit)
- **9/28 ~ 10/10** · M-111 ~ M-1100(批次 12 × 99 ~ 1000 条,覆盖 16 风格 + 8 情绪 + 5 BPM + 24 调性 × 60% 笛卡尔积)
- **10/11 ~ 10/31** · M-1101 ~ M-10000(目标 1 万条),按 100 批次入库,每 100 条 1 commit
- **并行** · mido 真链路接通(本骨架 v0 占位) + ChordProgression 提取真实化 + Tone.js 试听跨浏览器实测

## 不做什么

- **真实 .mid 二进制文件**(版权风险,见 `项目开发计划.md` §8):本骨架仅 metadata + 索引,Phase 1 续做时改用 CC 协议 / 用户自有
- **音频回放 URL**:Phase 1 用 Tone.js 加载本地 .mid,Phase 2 再外挂云端
- **向量相似度(余弦/Milvus)**:Phase 1 用标签筛选,Phase 2 再上 Milvus
- **.NET 量化 / 跨平台 DAW 拖拽**:Phase 2

## 历史

- **2026-09-18** · 批量入库脚手架 v0 落地(T5 03:00,本份):`batch_loader.py` 270 行 + 7 主体导出 + CLI 入口 + 14 测试用例 100% 通过,`项目开发计划.md` §5 第 88 项脚手架部分 checkbox `[x]` 闭环,§6 第 4 项留 M-011~M-110 真入库 + mido 真链路为续做
- **2026-09-17** · v0 目录骨架落地(T5 03:00):12 文件 ~520 行 Python + 90 行 TS + 330 行测试,31 用例 100% 通过,Phase 1 §6 第 4 项 checkbox `[x]` 闭环
- **2026-09-11** · 上游契约:`midi_tags_v0.json` T5 9/11 落库 4 维标签字典 + 5 示例 schema 锚点
- **2026-09-22 ~ 2026-09-26** · 原计划 §6 第 4 项节奏,9/17 提前 1 节点 → 9/22 收口更紧凑(13 天窗口 9/17 ~ 9/30)
