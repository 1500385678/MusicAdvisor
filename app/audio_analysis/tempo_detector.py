"""Tempo detector · librosa beat tracking → BPM + 拍点位置。

Phase 0 已在 analysis_demo/librosa_quicklook.py 跑通 librosa.beat.beat_track 真实链路;
v0 骨架提供接口契约与占位实现,Phase 1 续做切换为 librosa 真链路。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

import numpy as np

from app.audio_analysis.audio_loader import AudioData


@dataclass
class TempoResult:
    """节拍检测结果。

    Attributes:
        bpm: 每分钟节拍数,保留 2 位小数
        beat_times: 拍点位置(秒),列表
        beat_strength: 拍点强度(0-1),numpy 数组,与 beat_times 等长
        confidence: 检测置信度(0-1),基于 beat_strength 归一化
    """

    bpm: float
    beat_times: List[float]
    beat_strength: np.ndarray
    confidence: float

    def __repr__(self) -> str:
        return (
            f"TempoResult(bpm={self.bpm:.2f}, beats={len(self.beat_times)}, "
            f"confidence={self.confidence:.2f})"
        )


class TempoDetector:
    """BPM 检测器(librosa beat tracking 真实链路占位)。"""

    # 节拍档位(用于离散化提示)
    BPM_BUCKETS = [
        (60, 80, "slow/ballad"),
        (80, 100, "moderate"),
        (100, 120, "medium"),
        (120, 140, "uptempo"),
        (140, 180, "fast"),
        (180, 240, "very_fast"),
    ]

    def __init__(self, hop_length: int = 512) -> None:
        """初始化检测器。

        Args:
            hop_length: librosa 默认 hop_length,512 对应 ~23ms @22050Hz
        """
        self.hop_length = hop_length

    def detect(self, audio: AudioData) -> TempoResult:
        """检测 BPM 与拍点。

        Args:
            audio: AudioData 实例

        Returns:
            TempoResult 实例
        """
        # v0 骨架:返回 mock 数据(120 BPM,每秒 1 拍);Phase 1 替换为:
        # tempo, beats = librosa.beat.beat_track(y=audio.waveform, sr=audio.sample_rate,
        #                                         hop_length=self.hop_length)
        # beat_times = librosa.frames_to_time(beats, sr=audio.sample_rate,
        #                                     hop_length=self.hop_length)
        return self._mock_detect(audio)

    def _mock_detect(self, audio: AudioData) -> TempoResult:
        """Mock 检测:返回 120 BPM + 每秒 1 拍(占位)。"""
        duration = audio.duration_sec
        n_beats = int(duration)  # 每秒 1 拍
        beat_times = [float(i) for i in range(n_beats)]
        beat_strength = np.ones(n_beats, dtype=np.float32)
        return TempoResult(
            bpm=120.0,
            beat_times=beat_times,
            beat_strength=beat_strength,
            confidence=1.0,
        )

    @staticmethod
    def classify_bpm(bpm: float) -> str:
        """将 BPM 离散化到档位标签。"""
        for low, high, label in TempoDetector.BPM_BUCKETS:
            if low <= bpm < high:
                return label
        return "extreme"  # ≥240 或 <60


def detect_tempo(audio: AudioData) -> TempoResult:
    """便捷函数:直接检测节拍。"""
    return TempoDetector().detect(audio)