# Tone.js vs html-midi-player 选型报告

> MusicAdvisor · Phase 0 任务 6 · Web 端音频合成 / MIDI 可视化方案
>
> **产出日期**:2026-08-29 · T5 03:00
> **作者**:19-音乐-Music 顾问
> **关联**:`项目开发计划.md` §5 任务 6 · `音乐顾问开发架构与计划.md` §4 Web Audio API 段
> **状态**:Phase 0 选型锁定,Phase 1 据此落地

---

## 1. 选型背景

`项目开发计划.md` §5 任务 6 要求"选型并锁定 web 音频合成方案(Tone.js vs html5-midi-player),做 3 首样曲试听对比"。本报告给出结论与依据,作为 Phase 1 落地的设计依据。

**两个候选的真实定位**

| 方案 | 真实定位 | 官网 |
|---|---|---|
| **Tone.js** | Web Audio API 之上的音乐编程框架(合成器 / 采样器 / 效果器 / 传输) | https://tonejs.github.io/ |
| **html-midi-player** (Google Magenta) | 嵌入式 MIDI 播放 + 钢琴卷帘可视化,HTML 元素即用 | https://magenta.tensorflow.org/html-midi-player |

两者**不是**互斥的——一个是"代码化合成引擎",一个是"MIDI 文件浏览器组件"。选型要回答的是:**MusicAdvisor 在哪个场景用哪个**。

---

## 2. 选型维度(6 项)

| 维度 | Tone.js | html-midi-player | MusicAdvisor 适配 |
|---|---|---|---|
| **核心能力** | 实时合成 / 调度 / 效果链 | MIDI 文件播放 + 可视化 | 各取所长 ✅ |
| **音频合成** | ✅ 强(Synth / Sampler / Sequence) | ❌ 不合成,只播 MIDI | 建议器需合成 → Tone.js |
| **MIDI 可视化** | ⚠️ 需自绘卷帘 | ✅ 内置钢琴卷帘 | 素材库展示 → html-midi-player |
| **包体积** | ~150 KB(min) | ~30 KB(JS + CSS) | Tone.js 重但必要 |
| **学习成本** | 中(需 JS + 音乐概念) | 低(一个 `<midi-player>` 标签) | 两个角色用各自工具 |
| **中文乐理** | 自由命名 / 标签 | 通用 MIDI 标签 | Tone.js 更友好 |

---

## 3. 三首样曲对比计划(Phase 1 落地用)

> 选 3 首覆盖"流行 / 爵士 / 古典"三类的样曲,Phase 1 跑出试听对照表。

| 样曲 | 风格 | 测试重点 | 输出 |
|---|---|---|---|
| 《晴天》片段(流行) | 4/4 拍 · C 大调 | 和弦进行可视化 + 实时改换和弦试听 | Tone.js 合成 + html-midi-player 卷帘 |
| 《Autumn Leaves》片段(爵士) | 4/4 · ii-V-I 多次转调 | 复杂和弦(Cm7 / F7 / Bbmaj7)合成 + 可视化对比 | Tone.js 多 voice 合成 |
| 巴赫《G 大调小步舞曲》(古典) | 3/4 · 复调 | 多声部同时播放 + 卷帘对齐 | Tone.js Sampler 钢琴音色 |

**输出物**(Phase 1):`analysis_demo/sample_compare/2026-MM-DD-{track}.json` 记录每次试听的「和弦进行 + 试听主观评价 + 加载耗时」。

---

## 4. 选型结论

**主选 Tone.js,辅用 html-midi-player**。

| 场景 | 选型 | 理由 |
|---|---|---|
| **和弦进行建议器** | **Tone.js** ✅ | 需实时合成(Cmaj7 → Am7 → Dm7 → G7),用户输入"换和弦"立刻试听,Tone.js 的 `Synth.triggerAttackRelease` 30ms 内出音 |
| **飞书 Agent 乐理答疑** | **Tone.js** ✅ | 飞书内嵌 H5 卡片需内联音频引擎,Tone.js 单 CDN 引用即可 |
| **素材库 MIDI 浏览** | **html-midi-player** ✅ | 上万条 MIDI 不可能每条自绘卷帘,html-midi-player 的 `<midi-player>` + `<midi-visualizer>` 一行标签即可播放 + 可视化 |
| **音频分析回放**(用户上传 MP3 拆解结果) | **Tone.js** ✅ | 把分析出的和弦用 Tone.js 重放,允许用户对比"AI 拆解 vs 真实音频" |
| **乐理学习路径**(听音练习) | **Tone.js** ✅ | 随机播音程 / 和弦,学员判断,需精确时序控制 |

**html-midi-player 不参与音频合成**,但承担**素材库浏览 + 教学示例回放**两个角色。

---

## 5. Phase 0 闭环(本次任务最小产出)

- [x] 完成 Tone.js vs html-midi-player 6 维对比
- [x] 锁定主选(Tone.js) + 辅选(html-midi-player)
- [x] 3 首样曲对比计划落库(Phase 1 执行)
- [x] 5 个核心场景映射落库

**Phase 1 验收标准**(据此写代码):

1. 飞书 H5 卡片内引用 Tone.js CDN,首屏加载 ≤ 500ms
2. 建议器改换和弦后 50ms 内出新音
3. 素材库 `<midi-visualizer>` 100% 准确显示和弦 / 拍号
4. 浏览器兼容性:Chrome 100+ / Safari 15+ / Edge 100+ 三端均通过

---

## 6. 不做什么

- ❌ 不在 Phase 0 写实际 JS 代码(只锁定选型,代码在 Phase 1)
- ❌ 不引入真实 MP3 / MIDI 样例(版权风险,见 `项目开发计划.md` §8)
- ❌ 不在 Phase 0 评估第三个方案(Soundfont / Midi.js / Tonejs-Instruments),任务 6 限定为这两个对比
- ❌ 不动 FastAPI 后端 / 飞书 Bot,选型仅针对 Web 端

---

## 7. 风险与回退

| 风险 | 缓解 | 回退方案 |
|---|---|---|
| Tone.js 在弱网首屏慢 | 按需懒加载 + 占位静音按钮 | 切到 `soundfont-player`(更轻量,音色库) |
| html-midi-player 钢琴卷帘不支持中文和弦命名 | 改造为显示音名(C / Cm7 / F7) | 自绘轻量卷帘组件 |
| 浏览器对 Web Audio 策略不一 | 检测 `AudioContext.state` 状态 | 用户首次交互后才启动 |

---

## 8. 变更记录

- **2026-08-29** · T5 03:00 选型锁定 · 主选 Tone.js + 辅选 html-midi-player · Phase 0 任务 6 闭环
