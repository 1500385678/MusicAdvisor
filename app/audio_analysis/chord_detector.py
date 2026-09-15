"""Chord detector · chroma 特征 + 模板匹配 → 和弦时间线。

Phase 1 续做:基于 librosa.chroma + 24 大调/24 小调/7 常用和弦质量模板匹配,
输出 (start_time, end_time, chord_label) 三元组。
v0 骨架提供接口契约与占位实现。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

import numpy as np

from app.audio_analysis.audio_loader import AudioData


@dataclass
class ChordSegment:
    """单个和弦片段。

    Attributes:
        start_time: 起始时间(秒)
        end_time: 结束时间(秒)
        chord: 和弦符号(如 "C"、"Am"、"F"、"G7")
        confidence: 置信度(0-1)
    """

    start_time: float
    end_time: float
    chord: str
    confidence: float

    def duration(self) -> float:
        """片段时长。"""
        return self.end_time - self.start_time

    def __repr__(self) -> str:
        return (
            f"ChordSegment({self.start_time:.2f}s ~ {self.end_time:.2f}s, "
            f"{self.chord}, conf={self.confidence:.2f})"
        )


@dataclass
class ChordResult:
    """和弦识别结果。

    Attributes:
        segments: 时间线上的和弦片段列表
        vocabulary: 出现的和弦集合(去重)
        unique_count: 不同和弦数
    """

    segments: List[ChordSegment]
    vocabulary: List[str]
    unique_count: int

    def __repr__(self) -> str:
        return (
            f"ChordResult(segments={len(self.segments)}, "
            f"unique={self.unique_count}, vocab_size={len(self.vocabulary)})"
        )


class ChordDetector:
    """和弦检测器(chroma + 模板匹配占位)。"""

    # 24 大调 + 24 小调 + 7 常用和弦质量 = 48+ 模板
    CHORD_QUALITIES = ["", "m", "7", "maj7", "m7", "dim", "sus4"]
    # 注:24 调 × 7 质量 = 168 模板

    def __init__(self, hop_length: int = 512, min_segment_sec: float = 0.5) -> None:
        """初始化检测器。

        Args:
            hop_length: chroma 帧移
            min_segment_sec: 最短片段时长,短于此的片段与前邻合并
        """
        self.hop_length = hop_length
        self.min_segment_sec = min_segment_sec

    def detect(self, audio: AudioData) -> ChordResult:
        """检测和弦时间线。

        Args:
            audio: AudioData 实例

        Returns:
            ChordResult 实例
        """
        # v0 骨架:返回 mock I-V-vi-IV(C-Am-F-G)4 个和弦;
        # Phase 1 切换为:
        # chroma = librosa.feature.chroma_cqt(y=audio.waveform, sr=audio.sample_rate,
        #                                      hop_length=self.hop_length)
        # 模板匹配 → 帧级和弦 → 滑动窗口合并相邻同和弦 → 过滤短片段
        return self._mock_detect(audio)

    def _mock_detect(self, audio: AudioData) -> ChordResult:
        """Mock 检测:返回 I-V-vi-IV (C-G-Am-F) 4 个和弦占位。"""
        duration = audio.duration_sec
        n_chords = 4
        seg_dur = duration / n_chords
        chords = ["C", "G", "Am", "F"]
        segments = [
            ChordSegment(
                start_time=i * seg_dur,
                end_time=(i + 1) * seg_dur,
                chord=chords[i],
                confidence=0.80,
            )
            for i in range(n_chords)
        ]
        return ChordResult(
            segments=segments,
            vocabulary=chords,
            unique_count=len(chords),
        )


def detect_chords(audio: AudioData) -> ChordResult:
    """便捷函数:直接检测和弦。"""
    return ChordDetector().detect(audio)