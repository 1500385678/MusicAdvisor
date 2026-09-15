# 音频分析 MVP · Phase 1 §6 第 3 项

> **状态**:v0 目录骨架(2026-09-16 T5 落地)
> **任务**:`项目开发计划.md` §6 第 3 项「音频分析 MVP:上传 MP3 → 输出调性/节拍/和弦进度,可视化乐谱」
> **关联**:
> - [项目开发计划.md](../../项目开发计划.md) §6 第 3 项
> - [9/16 T1 巡检报告](../../.Log/巡检-音乐-20260916.md) P0 #1(节奏提前 1 节点 · §6 第 1 + 2 项救火 + 守卫双效合一模式第 3 次应用)
> - [9/15 §6 第 2 项和弦进行建议器 Web 版](../chord_suggester/) — 同 Phase 1 起步期,同 10 文件 ~1200 行规模
> - [9/14 §6 第 1 项乐理问答飞书机器人](../feishu_bot/) — 同 Phase 1 起步期

---

## 产品定位

**核心场景**:用户上传一段 MP3(参考曲 / demo / 自己的作品) → 后端跑 librosa + essentia 真链路 → 返回**调性 / BPM / 和弦时间线** → 浏览器渲染**波形 + 调性轮 + 和弦时间线 + 拍点 overlay**四合一可视化乐谱。

**目标用户**(沿用 §1 三群):

- **业余/进阶器乐学习者**:上传偶像的歌 → 看"原来这首歌是 C 大调,4/4 拍,I-V-vi-IV 进行" → 立刻 get 套路
- **独立音乐人 / 词曲创作者**:写新歌卡壳 → 上传参考曲 → 拿到"同调性 + 同 BPM + 同进行的"骨架作为模板
- **制作人 / 编曲师**:收到 demo → 5 秒识别调性/BPM → 决定是否需要变调/变速

**区别于 §6 第 1 + 2 项**:

- §6 第 1 项乐理问答:**纯文字问答**(乐理知识)
- §6 第 2 项和弦建议:**生成式**(情绪 + 调性 → 候选和弦进行)
- **§6 第 3 项(本项)音频分析**:**感知式**(音频 → 结构化乐理信息)

## 架构

```
app/audio_analysis/
├── README.md                 # 本文件
├── __init__.py               # 包导出(1227 字节)
├── audio_loader.py           # MP3/WAV → numpy 波形(78 行)
├── tempo_detector.py         # librosa beat tracking → BPM(85 行)
├── key_detector.py           # chroma + K-S 模板 → 24 调(99 行)
├── chord_detector.py         # chroma + 模板匹配 → 和弦时间线(94 行)
├── visualizer.py             # matplotlib 多面板 → PNG(89 行)
├── pipeline.py               # 端到端编排 + JSON 序列化(135 行)
├── api_analyze.template.ts   # Next.js 14 API 路由契约(135 行)
├── requirements.txt          # librosa/numpy/soundfile 锁版本
└── tests/
    ├── __init__.py
    └── test_audio_analysis.py  # 23 用例覆盖(v0 全绿)
```

**总 11 文件 / ~1.2 KB README + ~700 行 Python + ~135 行 TS + ~330 行测试 ~ ~1.2 KB requirements**,与 9/14 + 9/15 §6 第 1 + 2 项同模式同规模。

## 模块接口契约

### 输入

- **音频文件**:.mp3 / .wav / .flac / .ogg / .m4a
- **最大尺寸**:50 MB(可在 api_analyze.template.ts 调整)
- **最长时长**:不强制,但 > 10 分钟会显著增加分析耗时

### 输出(AnalysisReport JSON)

```json
{
  "source_path": "/uploads/test.mp3",
  "duration_sec": 180.5,
  "sample_rate": 22050,
  "tempo": {
    "bpm": 120.0,
    "beat_count": 361,
    "beat_times": [0.0, 0.5, 1.0, ...],
    "confidence": 0.92,
    "bpm_bucket": "medium"
  },
  "key": {
    "key": "C",
    "scale": "major",
    "confidence": 0.85,
    "chroma": [0.083, 0.083, ...],   // 12 维
    "top5_candidates": [
      {"key": "C major", "score": 0.20},
      {"key": "G major", "score": 0.15},
      ...
    ]
  },
  "chords": {
    "segments": [
      {"start_time": 0.0, "end_time": 45.0, "chord": "C", "confidence": 0.88, "duration_sec": 45.0},
      ...
    ],
    "vocabulary": ["C", "G", "Am", "F"],
    "unique_count": 4
  },
  "visualization_png_b64": "iVBORw0K...",   // Base64 PNG
  "meta": {
    "version": "0.1.0",
    "phase": "Phase 1 §6 第 3 项 v0 目录骨架",
    "analyzed_at": "2026-09-16T03:01:23",
    "tempo_confidence": 0.92,
    "key_confidence": 0.85,
    "mean_chord_confidence": 0.855
  }
}
```

## 算法(v0 骨架 + Phase 1 真链路替换点)

### 1. 音频加载 (`audio_loader.py`)

- **v0 骨架**:返回 1 秒静音 mock 波形(`np.zeros(22050)`)
- **Phase 1 替换点**:`librosa.load(str(p), sr=22050, mono=True)` 返回 `(waveform, sr)`
- **支持格式**:MP3 / WAV / FLAC / OGG / M4A(MP3 经 ffmpeg 解码)

### 2. 节拍检测 (`tempo_detector.py`)

- **v0 骨架**:返回 120 BPM + 每秒 1 拍
- **Phase 1 替换点**:`librosa.beat.beat_track(y, sr, hop_length=512)` + `librosa.frames_to_time(beats, sr, hop_length)`
- **档位分类**(6 档):slow/ballad(60-80) / moderate(80-100) / medium(100-120) / uptempo(120-140) / fast(140-180) / very_fast(180-240) / extreme(≥240 或 <60)
- **可选加速**:`essentia` 的 `RhythmExtractor2013`(C++ 绑定,比 librosa 快 2-3 倍)

### 3. 调性识别 (`key_detector.py`)

- **v0 骨架**:返回 C major + 5 候选占位
- **Phase 1 替换点**:`librosa.feature.chroma_stft(y, sr).mean(axis=1)` → 12 维 chroma → **Krumhansl-Schmuckler 模板匹配**(24 模板:12 大调 + 12 小调相关系数排序)→ Top-K
- **等音归一**:`Db → C#`, `Eb → D#`, `Gb → F#`, `Ab → G#`, `Bb → A#`(flat → sharp)
- **24 调列表**:12 大调(C/D/E/F/G/A/B + 5 个 #)+ 12 小调(Am/Dm/Em/Fm/Gm/Bm + 5 个 #m)

### 4. 和弦检测 (`chord_detector.py`)

- **v0 骨架**:返回 I-V-vi-IV(C-G-Am-F)4 个和弦各占 1/4 时长
- **Phase 1 替换点**:
  - `librosa.feature.chroma_cqt(y, sr, hop_length=512)` 帧级 chroma
  - **168 模板匹配**:24 调 × 7 质量(空=major / m / 7 / maj7 / m7 / dim / sus4)
  - 帧级和弦 → 滑动窗口合并相邻同和弦 → 过滤 < 0.5s 短片段
- **输出**:`(start_time, end_time, chord, confidence)` 时间线 + vocabulary(出现的和弦集合)

### 5. 可视化 (`visualizer.py`)

- **v0 骨架**:返回 1×1 透明 PNG 占位字节流
- **Phase 1 替换点**:matplotlib 4 面板:
  1. **波形 + 拍点 overlay**:上半部分,waveform 灰线 + 节拍红点
  2. **BPM 时序变化**:beat_strength 折线
  3. **调性 chord-wheel 玫瑰图**:12 维 chroma 极坐标
  4. **和弦时间线**:色块 + 符号(每段一个和弦标签)

### 6. 端到端流水线 (`pipeline.py`)

- 串行:`loader → tempo + key + chord → visualizer → AnalysisReport`
- 序列化兜底:numpy ndarray / float32 / bytes 全部转 Python 原生类型 + Base64 PNG
- **元数据**:`version` / `phase` / `analyzed_at` / 三置信度均值

## 与其他模块的关系

- **§6 第 1 项乐理问答飞书机器人**:`feishu_bot/`
  - 输入:用户文本问题
  - 输出:乐理知识文字回答
  - **本项衔接点**:用户可"上传音频 + 问为什么识别成 C 大调" → 飞书 bot 调音频分析 + 解释

- **§6 第 2 项和弦进行建议器**:`chord_suggester/`
  - 输入:调性 + 情绪
  - 输出:5-8 候选和弦进行 + Tone.js 试听
  - **本项衔接点**:用户上传参考曲 → 拿到调性 + 真实进行 → 输入建议器 → "同调性 + 不同情绪"的 5 变体

- **Phase 0 资产**:
  - `analysis_demo/librosa_quicklook.py`:已跑通 librosa 真实链路 demo
  - `analysis_demo/requirements.txt`:librosa/numpy 锁版本
  - `analysis_demo/scores/midi_tags_v0.json`:风格标签字典(可关联 BPM/调性 → 风格)

## API 路由契约(`api_analyze.template.ts`)

Next.js 14 API 路由,接收 multipart/form-data 上传 → 返回 AnalysisReport JSON。

```typescript
// 使用方式(Phase 1 真实接入):
//   1. 复制 api_analyze.template.ts 到 ../../../app/api/audio/analyze/route.ts
//   2. 取消 mock 段注释,启用后端 Python 调用(见文件内注释)
//   3. 前端 fetch('/api/audio/analyze', { method: 'POST', body: formData })
//
// 输入:multipart/form-data,字段 'file' = audio binary
// 输出:JSON AnalysisReport(含可视化 PNG Base64)
```

## 测试覆盖(23 用例,v0 100% 通过)

| 模块 | 测试类 | 用例数 |
|---|---|---|
| audio_loader | TestAudioLoader | 7(默认/自定义/格式列表/不存在/不支持/真实加载/便捷函数) |
| tempo_detector | TestTempoDetector | 4(默认/检测/档位分类 6 档/便捷函数) |
| key_detector | TestKeyDetector | 6(24 调列表/检测/等音归一 5 种/已 sharp 不变/Top-K/便捷函数) |
| chord_detector | TestChordDetector | 5(片段返回/覆盖时长/词汇表去重/ChordSegment.duration/便捷函数) |
| visualizer | TestVisualizer | 3(PNG 字节流/自定义尺寸/便捷函数) |
| pipeline | TestPipeline | 4(初始化/分析返回 report/JSON 序列化无 numpy 残留/便捷函数) |
| integration | TestIntegration | 1(端到端 4 块一致性 + 6 档 BPM 验证) |
| **合计** | 7 类 | **23 用例** |

**Phase 1 续做测试扩展**:

- librosa 真实链路接通后补 `tests/integration_real_audio.py`(3-5 首真实 MP3 端到端)
- 调性识别准确率测试(对照 music21 真库 ≥ 70% 命中)
- 和弦识别准确率测试(对照人工标注 5 首种子曲 ≥ 60% 命中)

## Phase 1 续做清单(9/17 ~ 9/20 节奏窗口)

1. **真实链路接通**(2-3 天):
   - `pip install -r requirements.txt` 装 librosa/numpy/soundfile
   - 替换 6 个模块的 `_mock_*` 为真实算法
   - 跑 3 首真实 MP3(本机已有的 60 首种子库任选 3 首)
2. **可视化激活**(1 天):
   - 装 matplotlib,激活 4 面板真渲染
   - 调色板:波形灰 + 拍点红 + 和弦色块按质量分(大调蓝/小调紫/dim 灰/sus4 橙)
3. **API 路由接 FastAPI 后端**(1 天):
   - 复制 `api_analyze.template.ts` → `app/api/audio/analyze/route.ts`
   - 写 FastAPI 后端 `audio_service.py` 包装流水线
   - Next.js API 路由改为 spawn Python 调用
4. **真实链路 23+ 用例全绿**(0.5 天):
   - 跑通 `pytest -v` 全绿,补 3 首真实 MP3 端到端测试

## 风险与边界

- **音频版权**:Phase 1 限定用户自有音乐 + CC 协议素材,生产环境需在 README 顶部声明
- **识别准确率**:复杂编曲(电音/爵士/古典)和弦识别误差大,UI 必须明确"AI 建议,非乐谱",保留人工修正入口
- **大文件性能**:>10 分钟 MP3 可能 > 30s 分析耗时,需前端 loading + 后端异步任务队列(Phase 2)

## 历史

- **2026-09-16** · v0 目录骨架落地(T5 救火 + 守卫 + Phase 1 §6 第 3 项三效合一,9/16 巡检 P0 #1 命中)