# analysis_demo · MusicAdvisor 音频分析 demo

> 19-音乐-Music · Phase 0 任务 5 最小可入库 demo
>
> **创建**:2026-08-28(T5 03:00 应急产出,T4 02:00 计划文件缺失,见 `.Log/巡检-音乐-20260828.md` P0/P1)
> **状态**:Phase 0 **占位脚本** —— 契约已固定,librosa + essentia 真实调用待 Phase 1 接入
> **关联**:`项目开发计划.md` §5 任务 5 · `音乐顾问开发架构与计划.md` §4 音频分析层

---

## 1. 文件清单

| 文件 | 行数 | 状态 | 说明 |
|---|---|---|---|
| `librosa_quicklook.py` | ~120 | Phase 0 占位 | mock 数据演示 4 维输出契约 |
| `requirements.txt` | ~30 | Phase 0 配套(2026-08-31 补) | 锁 librosa/essentia/numpy 版本,Phase 1 `pip install -r` 启用 |
| `tonejs_vs_midiplayer.md` | - | Phase 0 选型报告(2026-08-29) | Web 端合成方案选型结论,见 `§7` 关联 |
| `package.json` | ~30 | Phase 0/1 配套(2026-09-01 补) | 锁 Tone.js + @magenta/music + webcomponents 版本,Phase 1 `npm install` + `npm run dev` 启动静态 demo 服务器 |

---

## 2. 4 维输出契约(Phase 1 不变,只换数值源)

| 字段 | 类型 | Phase 0 占位值 | Phase 1 真实源 |
|---|---|---|---|
| `duration_sec` | float | 180.0 | `librosa.get_duration()` |
| `bpm` | float | 120.0 | `librosa.beat.beat_track()` |
| `key` | str | `"C major"` | chroma + K-S 模板匹配(essentia) |
| `chord_count` | int | 8 | chroma 变调次数统计 |

> **为什么先固定契约**:Phase 0 阶段调性 / BPM 算法可能换,但字段名 + 语义不变,这样后续 Web / Agent 端解析代码不需要随算法变更反复改。

---

## 3. 运行步骤

### 3.1 Phase 0 占位模式(无依赖)

```bash
cd /Users/aaron/Mac/Consultant/19-音乐-Music/_MusicLib/MusicWeb
python3 analysis_demo/librosa_quicklook.py
```

预期输出(JSON):
```json
{
  "file": "<mock>",
  "duration_sec": 180.0,
  "bpm": 120.0,
  "key": "C major",
  "chord_count": 8,
  "analyzed_at": "2026-08-28T03:00:00+0800"
}
```

### 3.2 Phase 1 真实模式(待启用)

1. 准备 1 首 ≥ 30s MP3 样例(用户自有 / CC 协议,见 `项目开发计划.md` §8 风险段)
2. `pip install -r analysis_demo/requirements.txt`(版本已锁,见 `requirements.txt`)
3. 取消 `librosa_quicklook.py` 内 `_analyze_with_librosa` 注释,补全 `_estimate_key_with_essentia` / `_count_chroma_transitions` 实现
4. `python3 analysis_demo/librosa_quicklook.py path/to/sample.mp3`

### 3.3 Web 端合成 · NPM 启动模式(2026-09-01 补)

> 适用:Phase 1 起步,跑通"Tone.js 实时合成 + html-midi-player 钢琴卷帘"两端的 demo 试听。

```bash
cd /Users/aaron/Mac/Consultant/19-音乐-Music/_MusicLib/MusicWeb
npm install --prefix analysis_demo        # 装 Tone.js + @magenta/music + webcomponents
cd analysis_demo
npm run check:deps                         # 验证 3 个核心依赖锁在 dependencies
npm run dev                                # 启动 http://localhost:5173 静态服务器
```

**锁版本**(见 `package.json`)

| 依赖 | 范围 | 角色 |
|---|---|---|
| `tone` | `^14.7.77` | 主选 · Web 音频合成引擎(实时和声 / 试听) |
| `@magenta/music` | `^1.23.0` | 辅选 · MIDI 转换 / NoteSequence 处理 |
| `@magenta/music-webcomponents` | `^0.5.1` | 辅选 · `<midi-player>` + `<midi-visualizer>` 钢琴卷帘 |
| `serve` (dev) | `^14.2.4` | `npm run dev` 静态服务器 |

> **不引入真实 MP3 / MIDI 样例**(版权风险,见 `项目开发计划.md` §8);Phase 1 demo 阶段仅在浏览器内用 Tone.js 合成 1 段 ii-V-I 验证 30ms 出音(`tonejs_vs_midiplayer.md` §5 验收第 2 条),不上传音频文件。

---

## 4. 验收标准

| 维度 | Phase 0 | Phase 1 |
|---|---|---|
| 脚本可运行 | ✅ 无依赖 | ✅ 真实 MP3 |
| 4 维输出稳定 | ✅ mock 固定值 | ✅ 算法稳定,允许浮动 |
| 字段契约 | ✅ 锁定 | ✅ 沿用 |
| README 完整 | ✅ 本文件 | ⏳ Phase 1 补 accuracy 报告 |

---

## 5. 不做什么

- ❌ 不在 Phase 0 强求真实 librosa / essentia 安装(Mac mini 无音频环境)
- ❌ 不动 Web 端 / 飞书端,只立仓库内最小可入库 demo
- ❌ 不引入外部 MP3 样例(版权风险,见 `项目开发计划.md` §8)

---

## 6. 变更记录

- **2026-08-28** · T5 03:00 应急创建,Phase 0 占位脚本,3 段式契约 + mock 数据 · 张勇 P0 巡检建议落地
- **2026-08-29** · T5 03:00 补 `tonejs_vs_midiplayer.md` 选型报告(见仓库 commit `6af1d6f`)
- **2026-08-31** · T5 03:00 补 `requirements.txt` 锁版本(librosa 0.10.x / essentia 2.1b6 / numpy 1.26.x),响应 8/29 巡检 P0 建议,让 Phase 1 真实模式从"占位"升级到"`pip install -r` 一键跑通";`README.md` §3.2 同步改为引用 requirements.txt
- **2026-09-01** · T5 03:00 补 `package.json` 锁 Tone.js(主)+ @magenta/music / webcomponents(辅)+ serve(dev),响应 9/1 巡检 P1 项(8/29 选型 + 9/1 起步准备),让 Phase 1 Web 端从"选型报告"升级到"`npm install` + `npm run dev` 一键试听"基础设施;`README.md` §1 文件清单 + §3.3 NPM 启动模式 + §1.4 锁版本表 同步落地
