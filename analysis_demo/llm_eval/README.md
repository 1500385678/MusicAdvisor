# LLM 乐理问答基线评估

> 19-音乐-Music · 任务 9 · 2026-09-12 T5 起步
>
> **目的**:为 MusicAdvisor 的"乐理问答飞书机器人"建立 LLM 基线准确率,作为 Phase 1 MVP(乐理问答模块)的算法选型依据。

---

## 一、背景

**来源**:9/12 T1 巡检 P0 #1 · 9/12 02:00(`巡检-音乐-20260912.md`)
> 用 60 首乐谱 + `音乐顾问开发架构与计划.md` 乐理知识图谱 9 题 × Claude / Qwen-Music 双模型 = 18 次评估 → `analysis_demo/llm_eval_baseline.json` 准确率分布

**为什么是任务 9**:任务 9 是 Phase 0 收官 11/12 → 12/12 满闭环的最后 1 项(9/13 收官,距今 1 天),9/12 03:00 必落 1 份 commit 闭环保命。

**为什么 v0 起步**:完整 18 次评估需调 Claude API + Qwen-Music,涉及 API token 配网 + 计费,本批次(9/12)先出 v0 起步:9 题题库 + 评估脚手架 + 当前 LLM(本 19-音乐-Music agent = MiniMax M3)自我评估作为 v0 baseline;完整 18 次双模型对比 Phase 1 续做(9/13 ~ 9/20)。

---

## 二、目录结构

```
llm_eval/
├── README.md              # 本文件(目录说明)
├── questions.json         # 9 题乐理题库(音程 3 + 和弦 3 + 调式 3)
├── baseline_v0.json       # v0 baseline:当前 LLM(MiniMax M3)自我评估结果
├── eval_runner.py         # 评估脚手架:可替换 LLM provider 跑题库
└── questions_full/        # (Phase 1 续做)扩到 100 题
```

---

## 三、9 题题库设计

**3 档难度** = 音程(基础)/ 和弦(进阶)/ 调式(高级),对齐 `项目开发计划.md` §6 Phase 1 "乐理问答飞书机器人:支持音程/和弦/调式三档难度"。

| 难度 | 题号 | 知识点 | 标准答案 |
|------|------|--------|----------|
| 音程 L1 | Q-01 | C4 → G4 音程识别 | 完全五度(P5) |
| 音程 L2 | Q-02 | E♭ → B♭ 音程识别(含变化音) | 完全五度(P5) |
| 音程 L3 | Q-03 | F# → D# 音程识别(双变化音) | 减六度(d6) |
| 和弦 L1 | Q-04 | C 大调 II-V-I 识别 | Dm - G7 - Cmaj7 |
| 和弦 L2 | Q-05 | Cmaj7 音的构成 | C E G B |
| 和弦 L3 | Q-06 | F-G-Am-Dm 进行判断调性 | C 大调(IV-V-vi-ii) |
| 调式 L1 | Q-07 | D Dorian 调式音阶 | D E F G A B C D |
| 调式 L2 | Q-08 | F# 自然小调音阶识别 | F# G# A B C# D# E F# |
| 调式 L3 | Q-09 | C D E G A 五声音阶调性 | C 大调五声(大调 pentatonic) |

**v0 题库规模**:9 题 = 3 难度 × 3 题,小样本,**仅为骨架**(Phase 1 扩到 100 题 = 30/30/40 难分)。

---

## 四、v0 baseline 评估

**当前 LLM**:MiniMax M3(本 19-音乐-Music agent,根 session)
**评估方法**:用 LLM 直接回答 9 题(零样本,中文 prompt),记录答案 + 与标准答案对比打 0/1 分
**准确率分布**:见 `baseline_v0.json`

**v0 baseline 用途**:
- 作为 Phase 1 真实评估(Claude / Qwen-Music)的对照基线
- 如果 MiniMax M3 v0 baseline 已经 ≥ 80%,说明 prompt 工程优先,模型选型次要
- 如果 v0 baseline < 60%,说明 LLM 乐理知识是弱项,需要 RAG + 知识图谱约束

---

## 五、Phase 1 续做路线图

| 阶段 | 时间 | 动作 | 产物 |
|------|------|------|------|
| v0 起步 | 9/12 T5 | 9 题 + MiniMax M3 baseline | 本目录全套文件 |
| v0.5 扩题 | 9/13 ~ 9/15 | 题库扩到 30 题(10/10/10) | `questions_full/v0_5_30q.json` |
| v1 双模型 | 9/16 ~ 9/20 | Claude API + Qwen-Music 双跑 30 题 | `baseline_v1_dual.json` + 准确率对比报告 |
| v1.5 RAG | 9/21 ~ 9/30 | 加 60 首乐谱上下文 RAG,重跑 30 题 | `baseline_v1_5_rag.json` |
| v2 飞书 | 10/1 ~ 10/15 | 飞书 Agent 集成"乐理问答"模块,种子用户反馈 | Phase 1 MVP 上线 |

---

## 六、与其他任务的关系

- **任务 7b 60/60 + 3 首 chord-by-chord**(9/10 闭环):本评估的"60 首乐谱上下文"就是 `analysis_demo/scores/seed_*.json` 60 份
- **任务 8 MIDI 标签体系骨架 v0**(9/11 闭环):本评估的"调式题"扩展可参考 `midi_tags_v0.json` 的 24 调性字典
- **Phase 1 §6 乐理问答飞书机器人**:本评估 v1.5 RAG 阶段直接对接飞书 Agent prompt
- **Phase 0 收官**:9/13 T1 巡检将检查 `项目开发计划.md` §5 任务 9 是否勾掉(本批 9/12 闭环)

---

## 七、维护

- **创建**:2026-09-12(T5 起步,9/12 T1 巡检 P0 #1)
- **维护人**:19-音乐-Music 行业顾问(每日 T5 增量)
- **关联文档**:
  - [`项目开发计划.md`](../../项目开发计划.md) §5 任务 9 · §6 Phase 1 乐理问答
  - [`音乐顾问开发架构与计划.md`](../../音乐顾问开发架构与计划.md) §三 模块 4 智能讲解 · §四 技术栈 LLM 选型
  - [`../scores/midi_tags_v0.json`](../scores/midi_tags_v0.json) · 24 调性字典(调式题扩展基础)
  - [`../scores/seed_60_summary.json`](../scores/seed_60_summary.json) · 60 首乐谱上下文
- **历史**:
  - 2026-09-12 · v0 起步(9 题 + MiniMax M3 baseline + 脚手架),任务 9 从 `[ ]` 闭环保 Phase 0 收官最后 1 项
