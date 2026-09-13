# 乐理问答飞书机器人 · Phase 1 §6 第 1 项

> **状态**:v0 目录骨架(2026-09-14 T5 落地)
> **任务**:`项目开发计划.md` §6 第 1 项「乐理问答飞书机器人:支持音程/和弦/调式三档难度,带钢琴键可视化」
> **关联**:
> - [项目开发计划.md](../../项目开发计划.md) §6 第 1 项
> - [9/14 T1 巡检报告](../../.Log/巡检-音乐-20260914.md) P0 #1
> - [9/12 任务 9 LLM 乐理问答基线评估 v0](../../analysis_demo/llm_eval/) — 同源 LLM 脚手架

---

## 产品定位

飞书入口为主、Web 端为辅的乐理答疑机器人,定位 3 类用户:

- **器乐学习者**(钢琴/吉他):问"小三度是多少半音?"→ 答 + 钢琴键 SVG
- **独立音乐人 / 词曲创作者**:问"属七和弦怎么用?"→ 答 + 5-8 候选和弦
- **制作人 / 编曲师**:问"Dorian 调式和自然小调差在哪?"→ 答 + 5 声音阶 + 9/13 和弦链

三档难度(对应 9/12 任务 9 题库结构):

| 档位 | 题目类型 | v0 覆盖 | Phase 1 9/15 ~ 9/20 目标 |
|------|----------|---------|--------------------------|
| 入门 | 音程识别 / 三和弦构成 | 12 音程 + 7 和弦 | 27 音程 + 20+ 和弦 |
| 进阶 | 七和弦 / 自然/和声/旋律小调 | 7 和弦 + 7 调式 | 50+ 和弦 + 12 调式 |
| 高级 | 教会调式 / 五声音阶 / 蓝调 | 7 调式 | 12 调式 + 5 五声 + 3 日本民谣 |

## 架构

```
[飞书用户]──Lark Webhook──┐
                          ▼
              FastAPI (main.py)
                          │
                ┌─────────┼─────────┐
                ▼         ▼         ▼
         handlers/    llm_     piano_
         music_theory client   visualizer
                │         │         │
                ▼         ▼         ▼
        music_theory_  LLM API    SVG 渲染
        lib (本地)    (Phase 1)  (Markdown 内嵌)
```

## 文件结构

```
app/feishu_bot/
├── README.md              ← 本文件
├── __init__.py            ← 公开 API
├── main.py                ← FastAPI app + webhook 入口
├── config.py              ← 配置(env 读飞书 app_id/secret/token)
├── handlers/
│   └── music_theory.py    ← 乐理问答 handler(音程/和弦/调式)
├── llm_client.py          ← LLM 客户端(对接 llm_eval 脚手架)
├── music_theory_lib.py    ← 乐理基础数据(12+7+7)
├── piano_visualizer.py    ← 钢琴键 SVG 渲染器
├── requirements.txt       ← 依赖
└── tests/
    └── test_smoke.py      ← 烟测 7 条
```

## Phase 1 落地计划(9/15 ~ 9/30)

| 周 | 任务 | 依赖 |
|----|------|------|
| 9/15 ~ 9/20 | 真飞书 app_id 接入 + LLMClient 真调 + 88 键全键盘 | 飞书后台 + .env 配 |
| 9/21 ~ 9/25 | 题库扩 100 题 + RAG 增强 + 错例反馈 | 9/12 任务 9 baseline v0 |
| 9/26 ~ 9/30 | 邀请 20 个种子用户试用 + 收集"识别准确率"反馈 | 飞书用户群 + 邀请 |

## 不做什么(本期 v0 骨架)

- ❌ 不接真飞书 app_id(env 全空,FastAPI 起来即可)
- ❌ 不真调 LLM(LLMClient.ask() 返回占位文本)
- ❌ 不做 88 键全键盘(只 1 八度 7 白键 + 5 黑键)
- ❌ 不做 Web UI(Phase 1 §6 第 2 项"和弦建议器 Web"再做)

## 验证方式

```bash
cd /Users/aaron/Mac/Consultant/19-音乐-Music/_MusicLib/MusicWeb
pip install -r app/feishu_bot/requirements.txt
pytest app/feishu_bot/tests/test_smoke.py -v
# 8 用例 7/8 通过(测试 healthz 需先 pip install,1 个 example 在 v0 占位)
```

## 历史

- **2026-09-14** · T5 目录骨架 v0 落地(11 文件 350 行,1 commit 闭环)
  - Phase 0 12/12 满后 Phase 1 起步第 1 项
  - 9/14 T1 巡检 P0 #1 命中(救火 + 守卫双效合一)
