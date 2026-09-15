"""Audio visualizer · 波形 + BPM + 调性 + 和弦时间线 → matplotlib PNG。

Phase 1 续做:多面板可视化(上波形 + 中 BPM/调性 + 下和弦时间线);
v0 骨架提供接口契约与 mock PNG,Phase 1 切换为 matplotlib 多面板真实渲染。
"""

from __future__ import annotations

import io
from dataclasses import dataclass
from typing import Tuple

import numpy as np

from app.audio_analysis.audio_loader import AudioData
from app.audio_analysis.chord_detector import ChordResult
from app.audio_analysis.key_detector import KeyResult
from app.audio_analysis.tempo_detector import TempoResult


@dataclass
class VisualizationResult:
    """可视化结果。

    Attributes:
        image_bytes: PNG 字节流(便于 HTTP 直接返回 image/png)
        width: 图像宽度(像素)
        height: 图像高度(像素)
        panels: 面板数(波形/BPM/调性/和弦)
    """

    image_bytes: bytes
    width: int
    height: int
    panels: int

    def __repr__(self) -> str:
        return (
            f"VisualizationResult({self.width}x{self.height}px, "
            f"{self.panels} panels, {len(self.image_bytes)} bytes)"
        )


class AudioVisualizer:
    """音频分析可视化器(multi-panel matplotlib 占位)。"""

    DEFAULT_DPI = 100
    DEFAULT_WIDTH_INCH = 12
    DEFAULT_HEIGHT_INCH = 8

    def __init__(self, width: int = 1200, height: int = 800) -> None:
        """初始化可视化器。

        Args:
            width: 输出图像宽度(像素)
            height: 输出图像高度(像素)
        """
        self.width = width
        self.height = height

    def render(
        self,
        audio: AudioData,
        tempo: TempoResult,
        key: KeyResult,
        chords: ChordResult,
    ) -> VisualizationResult:
        """渲染可视化图像。

        Args:
            audio: AudioData
            tempo: TempoResult
            key: KeyResult
            chords: ChordResult

        Returns:
            VisualizationResult
        """
        # v0 骨架:返回 1x1 透明 PNG 占位(无 matplotlib 真实依赖)
        # Phase 1 切换为 matplotlib 4 面板:
        #   1. 波形 + 拍点位置 overlay
        #   2. BPM 时序变化(beat strength 折线)
        #   3. 调性 chord-wheel 玫瑰图
        #   4. 和弦时间线(色块 + 符号)
        return self._mock_render(audio, tempo, key, chords)

    def _mock_render(
        self,
        audio: AudioData,
        tempo: TempoResult,
        key: KeyResult,
        chords: ChordResult,
    ) -> VisualizationResult:
        """Mock 渲染:返回最小 PNG 字节流。"""
        # 最小合法 PNG(1x1 透明)
        png_bytes = (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
            b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\xfc\xff"
            b"\xff?\x00\x05\xfe\x02\xfe\xa3\xc9\xff\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        return VisualizationResult(
            image_bytes=png_bytes,
            width=self.width,
            height=self.height,
            panels=4,
        )


def visualize_analysis(
    audio: AudioData,
    tempo: TempoResult,
    key: KeyResult,
    chords: ChordResult,
) -> VisualizationResult:
    """便捷函数:渲染分析结果可视化。"""
    return AudioVisualizer().render(audio, tempo, key, chords)