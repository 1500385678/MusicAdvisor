"""
librosa_quicklook.py · MusicAdvisor 音频分析 demo(Phase 0 占位)

==========================================================================
项目:    MusicAdvisor
模块:    Phase 0 / 任务 5 最小可入库 demo
作者:    19-音乐-Music 顾问(T5 03:00 应急产出)
日期:    2026-08-28
状态:    Phase 0 占位(脚本骨架,真实 librosa 调用待 Phase 1 接入)
关联:    项目开发计划.md §5 任务 5
         音乐顾问开发架构与计划.md §4 音频分析层
==========================================================================

设计意图
--------
1. Phase 0 不强求真实跑通,只先固定"输入 → 输出"契约,让后续 lib 替换有锚点
2. 当前用 mock 数据演示"上传 MP3 → 调性 / BPM / 时长 / 估计和弦数" 4 维输出
3. librosa + essentia 真实调用集中在 `_analyze_with_librosa()`,Phase 1 替换 mock

运行方式
--------
    # Phase 0 占位模式(无任何依赖):
    python analysis_demo/librosa_quicklook.py

    # Phase 1 真实模式(需 pip install librosa numpy):
    # 1) 取消 _analyze_with_librosa 注释
    # 2) 准备 1 首 ≥ 30s 的 MP3 样例(用户自有 / CC 协议)
    # 3) python analysis_demo/librosa_quicklook.py path/to/sample.mp3
"""
from __future__ import annotations

import json
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# 1. 输出契约 —— 4 维分析结果(Phase 1 真实跑通后字段不变,只换数值源)
# ---------------------------------------------------------------------------
@dataclass
class AudioAnalysisResult:
    file: str                       # 输入文件路径(占位时为 "<mock>")
    duration_sec: float             # 时长(秒)
    bpm: float                      # 节拍速度
    key: str                        # 估计调性,如 "C major" / "A minor"
    chord_count: int                # 估计独立和弦数(粗粒度)
    analyzed_at: str                # 分析时间戳(ISO 8601)


# ---------------------------------------------------------------------------
# 2. 占位实现 —— 当前用 mock 数据,Phase 1 替换
# ---------------------------------------------------------------------------
def _analyze_mock(audio_path: Optional[str]) -> AudioAnalysisResult:
    """Phase 0 占位:返回固定 mock 结果,用于契约验证与 README 演示。"""
    return AudioAnalysisResult(
        file=audio_path or "<mock>",
        duration_sec=180.0,         # 3 分钟样曲占位
        bpm=120.0,                  # 中速流行曲
        key="C major",              # 最常见调性
        chord_count=8,              # 流行曲 4-8 个独立和弦常见
        analyzed_at=time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime()),
    )


def _analyze_with_librosa(audio_path: str) -> AudioAnalysisResult:
    """Phase 1 真实实现 —— 当前为注释占位,Phase 1 取消注释即可。

    真实调用约定:
        import librosa
        import numpy as np

        y, sr = librosa.load(audio_path, sr=22050, mono=True)
        duration = librosa.get_duration(y=y, sr=sr)
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        key_estimate = _estimate_key_with_essentia(y, sr)  # chroma + K-S 模板
        chord_count = _count_chroma_transitions(y, sr)      # chroma 变调次数
    """
    raise NotImplementedError(
        "Phase 0 占位:librosa + essentia 真实调用待 Phase 1 接入。"
        "Phase 1 取消 _analyze_with_librosa 注释,补全依赖即可。"
    )


# ---------------------------------------------------------------------------
# 3. 入口
# ---------------------------------------------------------------------------
def analyze(audio_path: Optional[str] = None) -> AudioAnalysisResult:
    """统一入口 —— 占位模式永远可用,真实模式 Phase 1 启用。"""
    if audio_path is None:
        return _analyze_mock(None)
    return _analyze_with_librosa(audio_path)


def main() -> int:
    audio_arg = sys.argv[1] if len(sys.argv) > 1 else None
    if audio_arg is not None and not Path(audio_arg).exists():
        print(f"[ERROR] 文件不存在: {audio_arg}", file=sys.stderr)
        return 1
    result = analyze(audio_arg)
    print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
