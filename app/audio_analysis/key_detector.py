"""Key detector · librosa + essentia → 24 调(C/Am/D/Dm/...).

Phase 0 已在 analysis_demo/librosa_quicklook.py 跑通 chroma 特征提取;
v0 骨架提供接口契约与占位实现,Phase 1 续做切换为 chroma + Krumhansl-Schmuckler
模板匹配真链路。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

import numpy as np

from app.audio_analysis.audio_loader import AudioData

# 24 调(12 大调 + 12 小调)
KEY_NAMES_MAJOR = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]
KEY_NAMES_MINOR = ["Am", "Cm", "Dm", "Ebm", "Em", "Fm", "F#m", "Gm", "Abm", "Am", "Bbm", "Bm"]
# 等音修正(避免重复)
KEY_NAMES_MINOR = ["Am", "Bm", "Cm", "Dm", "Ebm", "Em", "Fm", "F#m", "Gm", "Abm", "Bbm", "C#m"]


@dataclass
class KeyResult:
    """调性识别结果。

    Attributes:
        key: 主调字符串(如 "C"、"Am"、"F#")
        scale: "major" 或 "minor"
        confidence: 置信度(0-1)
        chroma: 12 维 chroma 均值向量(便于可视化)
        candidates: 候选 Top-K,[(key, score), ...] 默认 Top 5
    """

    key: str
    scale: str
    confidence: float
    chroma: np.ndarray  # shape (12,)
    candidates: List[tuple]  # [(key_full, score), ...]

    def __repr__(self) -> str:
        return (
            f"KeyResult({self.key} {self.scale}, confidence={self.confidence:.2f}, "
            f"top5={len(self.candidates)})"
        )


class KeyDetector:
    """调性识别器(chroma + Krumhansl-Schmuckler 模板占位)。"""

    # Krumhansl-Schmuckler 模板(经典调性特征向量)
    MAJOR_PROFILE = np.array(
        [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
    )
    MINOR_PROFILE = np.array(
        [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]
    )

    def __init__(self, top_k: int = 5) -> None:
        """初始化检测器。

        Args:
            top_k: 返回 Top-K 候选,默认 5
        """
        self.top_k = top_k

    def detect(self, audio: AudioData) -> KeyResult:
        """识别调性。

        Args:
            audio: AudioData 实例

        Returns:
            KeyResult 实例
        """
        # v0 骨架:返回 mock C major;Phase 1 切换为:
        # chroma = librosa.feature.chroma_stft(y=audio.waveform, sr=audio.sample_rate).mean(axis=1)
        # 24 模板相关系数排序 → Top-K
        return self._mock_detect(audio)

    def _mock_detect(self, audio: AudioData) -> KeyResult:
        """Mock 识别:返回 C major + 等概率候选(占位)。"""
        chroma = np.ones(12, dtype=np.float32) / 12.0
        candidates = [
            ("C major", 0.20),
            ("G major", 0.15),
            ("F major", 0.10),
            ("Am minor", 0.10),
            ("D minor", 0.05),
        ]
        return KeyResult(
            key="C",
            scale="major",
            confidence=0.85,
            chroma=chroma,
            candidates=candidates[: self.top_k],
        )

    @staticmethod
    def normalize_key(raw_key: str) -> str:
        """等音归一(flat → sharp),返回统一格式。

        例: "Db" → "C#", "Bb" → "A#", "Eb" → "D#"
        """
        flat_to_sharp = {
            "Db": "C#",
            "Eb": "D#",
            "Gb": "F#",
            "Ab": "G#",
            "Bb": "A#",
        }
        return flat_to_sharp.get(raw_key, raw_key)

    @staticmethod
    def all_keys() -> List[str]:
        """返回 24 调字符串列表(12 大 + 12 小)。"""
        return list(KEY_NAMES_MAJOR) + list(KEY_NAMES_MINOR)


def detect_key(audio: AudioData) -> KeyResult:
    """便捷函数:直接识别调性。"""
    return KeyDetector().detect(audio)