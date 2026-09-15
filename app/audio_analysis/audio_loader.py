"""Audio loader · MP3/WAV → numpy 波形 + 采样率。

Phase 1 真实模式使用 librosa.load(Phase 0 demo 已跑通,见 analysis_demo/librosa_quicklook.py);
v0 骨架提供接口契约与 mock 实现,Phase 1 续做时切换为 librosa.load。
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Union

PathLike = Union[str, os.PathLike]


@dataclass
class AudioData:
    """音频数据容器。

    Attributes:
        waveform: 一维 numpy 数组(单声道),浮点 [-1, 1]
        sample_rate: 采样率(Hz),默认 22050(librosa 默认)
        duration_sec: 时长(秒)
        source_path: 源文件路径(便于可视化标注)
    """

    waveform: "object"  # numpy.ndarray,类型注解延迟避免引入 numpy 依赖
    sample_rate: int
    duration_sec: float
    source_path: str

    def __repr__(self) -> str:
        return (
            f"AudioData(duration={self.duration_sec:.2f}s, sr={self.sample_rate}Hz, "
            f"path={self.source_path})"
        )


class AudioLoader:
    """音频加载器。

    支持格式:
        - MP3(优先 librosa,回退 audioread + ffmpeg)
        - WAV(native scipy.io.wavfile / soundfile)
        - FLAC / OGG / M4A(依赖 librosa + ffmpeg)
    """

    SUPPORTED_FORMATS = {".mp3", ".wav", ".flac", ".ogg", ".m4a"}

    def __init__(self, target_sr: int = 22050, mono: bool = True) -> None:
        """初始化加载器。

        Args:
            target_sr: 目标采样率,默认 22050(librosa 默认,适合音乐分析)
            mono: 是否强制单声道,默认 True
        """
        self.target_sr = target_sr
        self.mono = mono

    def load(self, path: PathLike) -> AudioData:
        """加载音频文件。

        Args:
            path: 文件路径(.mp3 / .wav / ...)

        Returns:
            AudioData 实例

        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 不支持的格式
            RuntimeError: librosa 加载失败(Phase 1 真实模式可能)
        """
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"音频文件不存在: {p}")
        if p.suffix.lower() not in self.SUPPORTED_FORMATS:
            raise ValueError(
                f"不支持的音频格式: {p.suffix}(支持: {sorted(self.SUPPORTED_FORMATS)})"
            )

        # v0 骨架:返回 mock 数据;Phase 1 切换为 librosa.load 真实链路
        # y, sr = librosa.load(str(p), sr=self.target_sr, mono=self.mono)
        waveform, sr = self._mock_load(p)
        duration = len(waveform) / sr
        return AudioData(
            waveform=waveform,
            sample_rate=sr,
            duration_sec=duration,
            source_path=str(p.absolute()),
        )

    def _mock_load(self, p: Path) -> tuple:
        """Mock 加载 — 用于 v0 骨架测试,Phase 1 替换为 librosa.load。"""
        # 生成 1 秒的静音 mock 波形(供单元测试用,无外部依赖)
        import numpy as np

        n_samples = self.target_sr  # 1 秒
        waveform = np.zeros(n_samples, dtype=np.float32)
        return waveform, self.target_sr


def load_audio(path: PathLike, target_sr: int = 22050) -> AudioData:
    """便捷函数:直接加载音频文件。"""
    return AudioLoader(target_sr=target_sr).load(path)