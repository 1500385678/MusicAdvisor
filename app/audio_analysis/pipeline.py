"""Audio analysis pipeline · MP3 → {tempo, key, chords, beats, viz} JSON 编排。

v0 骨架:串行编排 audio_loader → tempo/key/chord → visualizer,
返回结构化 AnalysisReport(JSON 可序列化)。Phase 1 续做替换模块内 mock 为真链路。
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Dict, List

import numpy as np

from app.audio_analysis.audio_loader import AudioData, AudioLoader
from app.audio_analysis.chord_detector import ChordDetector, ChordResult
from app.audio_analysis.key_detector import KeyDetector, KeyResult
from app.audio_analysis.tempo_detector import TempoDetector, TempoResult
from app.audio_analysis.visualizer import AudioVisualizer, VisualizationResult


@dataclass
class AnalysisReport:
    """完整音频分析报告(JSON 可序列化)。

    Attributes:
        source_path: 源文件
        duration_sec: 时长
        sample_rate: 采样率
        tempo: BPM 与拍点信息(dict)
        key: 调性信息(dict)
        chords: 和弦时间线(dict)
        visualization_png_b64: 可视化 PNG(Base64,便于 HTTP 直接嵌入)
        meta: 元数据(版本/时间戳/置信度均值)
    """

    source_path: str
    duration_sec: float
    sample_rate: int
    tempo: Dict
    key: Dict
    chords: Dict
    visualization_png_b64: str
    meta: Dict = field(default_factory=dict)

    def to_json(self, indent: int = 2) -> str:
        """转为 JSON 字符串。"""
        return json.dumps(asdict(self), indent=indent, ensure_ascii=False, default=_json_default)

    def to_dict(self) -> Dict:
        """转为 dict。"""
        return asdict(self)


def _json_default(obj):
    """numpy → python 原生类型,JSON 序列化兜底。"""
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, np.floating):
        return float(obj)
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, (bytes, bytearray)):
        import base64

        return base64.b64encode(obj).decode("ascii")
    raise TypeError(f"不可序列化类型: {type(obj)}")


class AudioAnalysisPipeline:
    """端到端音频分析流水线。"""

    def __init__(
        self,
        target_sr: int = 22050,
        hop_length: int = 512,
        viz_width: int = 1200,
        viz_height: int = 800,
    ) -> None:
        """初始化流水线(参数透传到各模块)。"""
        self.loader = AudioLoader(target_sr=target_sr)
        self.tempo_detector = TempoDetector(hop_length=hop_length)
        self.key_detector = KeyDetector(top_k=5)
        self.chord_detector = ChordDetector(hop_length=hop_length)
        self.visualizer = AudioVisualizer(width=viz_width, height=viz_height)

    def analyze(self, path: str) -> AnalysisReport:
        """端到端分析音频文件。

        Args:
            path: 音频文件路径(.mp3 / .wav / ...)

        Returns:
            AnalysisReport 实例(含可视化 PNG Base64)
        """
        # 1. 加载
        audio = self.loader.load(path)

        # 2. 检测
        tempo = self.tempo_detector.detect(audio)
        key = self.key_detector.detect(audio)
        chords = self.chord_detector.detect(audio)

        # 3. 可视化
        viz = self.visualizer.render(audio, tempo, key, chords)

        # 4. 组装报告
        import base64
        import datetime

        return AnalysisReport(
            source_path=audio.source_path,
            duration_sec=audio.duration_sec,
            sample_rate=audio.sample_rate,
            tempo={
                "bpm": tempo.bpm,
                "beat_count": len(tempo.beat_times),
                "beat_times": tempo.beat_times,
                "confidence": tempo.confidence,
                "bpm_bucket": TempoDetector.classify_bpm(tempo.bpm),
            },
            key={
                "key": key.key,
                "scale": key.scale,
                "confidence": key.confidence,
                "chroma": key.chroma.tolist() if hasattr(key.chroma, "tolist") else list(key.chroma),
                "top5_candidates": [
                    {"key": k, "score": s} for k, s in key.candidates
                ],
            },
            chords={
                "segments": [
                    {
                        "start_time": seg.start_time,
                        "end_time": seg.end_time,
                        "chord": seg.chord,
                        "confidence": seg.confidence,
                        "duration_sec": seg.duration(),
                    }
                    for seg in chords.segments
                ],
                "vocabulary": chords.vocabulary,
                "unique_count": chords.unique_count,
            },
            visualization_png_b64=base64.b64encode(viz.image_bytes).decode("ascii"),
            meta={
                "version": "0.1.0",
                "phase": "Phase 1 §6 第 3 项 v0 目录骨架",
                "analyzed_at": datetime.datetime.now().isoformat(),
                "tempo_confidence": tempo.confidence,
                "key_confidence": key.confidence,
                "mean_chord_confidence": (
                    float(np.mean([s.confidence for s in chords.segments]))
                    if chords.segments
                    else 0.0
                ),
            },
        )


def analyze_audio(path: str) -> AnalysisReport:
    """便捷函数:直接分析音频文件,返回报告。"""
    return AudioAnalysisPipeline().analyze(path)