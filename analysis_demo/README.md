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
| `Dockerfile` | ~50 | Phase 0/1 配套(2026-09-02 补) | python:3.11-slim 容器化,Phase 1 `docker build` + `docker run` 跑通 librosa + essentia |
| `scores/seed_10.json` + `score_seed.py` | 10 首 / ~150 | Phase 0 任务 7a 起步(2026-09-04 补) | 流行 4 + 爵士 3 + 古典 3 种子乐谱契约 + 加载校验脚本,任务 7 总目标 50 首的 1/5 |
| `scores/seed_20_b.json` + `score_seed.py --batch all` | 20 首 / ~150 | Phase 0 任务 7b 第 2 批(2026-09-06 补) | 摇滚 5 + 民谣 5 + 电子 5 + 世界音乐 5 种子乐谱(契约同 7a),合并后 30/50 = 60%,见 `seed_30_summary.json`,7b 第 3 批 20 首 + 第 4 批 10 首待 9/8 ~ 9/12 续做 |

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

### 3.4 Docker 容器模式(2026-09-02 补)

> 适用:Phase 1 起步,需要 librosa + essentia 的可复现环境(Mac mini 无音频 / CI 跑全量验收)。

```bash
cd /Users/aaron/Mac/Consultant/19-音乐-Music/_MusicLib/MusicWeb/analysis_demo
docker build -t musicadvisor-analysis .           # ~3-5 分钟(拉 slim + 装 essentia wheel)
docker run --rm musicadvisor-analysis              # 跑占位模式,4 维输出
docker run --rm -v "$PWD":/data musicadvisor-analysis /data/sample.mp3   # Phase 1 真实模式(待 lib 接入)
```

**镜像选型**
- `python:3.11-slim`(非 alpine):避开 musl 编译坑,essentia wheel 在 glibc 段稳定
- 系统依赖:`ffmpeg` + `libsndfile1`(librosa 读 WAV / essentia 解码 MP3 必需)
- 分层缓存:先 `COPY requirements.txt` 再 `COPY *.py`,代码变更不触发 `pip install`
- 入口暂用 CLI(`librosa_quicklook.py`),FastAPI 服务留 Phase 1 接入

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
- **2026-09-02** · T5 03:00 补 `Dockerfile` + `.gitignore` 补 5 行,响应 9/1 巡检 P1 项(后端 FastAPI 起步 + 工程化补全):`Dockerfile` 选 `python:3.11-slim`(避 musl)+ ffmpeg / libsndfile1 + 分层 COPY requirements(代码变更不触发 pip 重装),入口暂用 CLI(FastAPI 服务留 Phase 1);`.gitignore` 补 `*.pyc` / `.ipynb_checkpoints/` / `data/` / `models/` / `dist/` / `.next/`(Phase 1 起步预备);`README.md` §1 文件清单 + §3.4 Docker 容器模式 同步落地
- **2026-09-04** · T5 03:00 启动 Phase 0 任务 7a(10 首种子乐谱),响应 9/4 巡检 P0(连续 3 巡检 0 推进,距 Phase 0 收官 2 天窗口):建 `scores/seed_10.json`(流行 4 + 爵士 3 + 古典 3,字段契约:key/scale/time_signature/bpm/chord_progression/tags 等 14 项)+ `score_seed.py`(无依赖标准库加载 + 契约校验 + 4 维汇总);`项目开发计划.md` §5 任务 7 拆为 7a(本批 10/50,已勾)/ 7b(续做 40 首);`README.md` §1 文件清单 + §6 变更记录 同步落地
- **2026-09-06** · T5 03:00 启动 Phase 0 任务 7b 第 2 批 20 首,响应 9/6 巡检 P0(9/4 起步 10/50 后 9/5 ~ 9/6 已 48h 0 续做,距 9/13 收官 7 天):建 `scores/seed_20_b.json`(摇滚 5 + 民谣 5 + 电子 5 + 世界音乐 5 = 20 首 S-011~S-030,同 7a 契约,ID 全局唯一);`score_seed.py` 升级到 batch 模式(注册表 BATCHES + --batch seed_10|seed_20_b|all + load_all 合并),`scores/seed_30_summary.json` 30/50 = 60% 汇总;`项目开发计划.md` §5 任务 7b 拆为已勾 20 首 + 余 20 首 + chord-by-chord 细粒度待 9/8 ~ 9/12 续做
