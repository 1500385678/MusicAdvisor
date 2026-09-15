"""Audio analysis MVP package.

Phase 1 §6 第 3 项 · 上传 MP3 → 输出 调性/节拍/和弦进度 + 可视化乐谱。

本包为 v0 目录骨架,流水线接口稳定但部分算法为占位实现,Phase 1 续做时替换为
librosa + essentia 真链路(参见 analysis_demo/librosa_quicklook.py 跑通 demo)。
"""

from app.audio_analysis.audio_loader import AudioLoader, load_audio
from app.audio_analysis.tempo_detector import TempoDetector, detect_tempo
from app.audio_analysis.key_detector import KeyDetector, detect_key
from app.audio_analysis.chord_detector import ChordDetector, detect_chords
from app.audio_analysis.visualizer import AudioVisualizer, visualize_analysis
from app.audio_analysis.pipeline import AudioAnalysisPipeline, analyze_audio

__version__ = "0.1.0"
__phase__ = "Phase 1 §6 第 3 项 v0 目录骨架"

__all__ = [
    # 数据加载
    "AudioLoader",
    "load_audio",
    # 节拍检测
    "TempoDetector",
    "detect_tempo",
    # 调性识别
    "KeyDetector",
    "detect_key",
    # 和弦检测
    "ChordDetector",
    "detect_chords",
    # 可视化
    "AudioVisualizer",
    "visualize_analysis",
    # 端到端流水线
    "AudioAnalysisPipeline",
    "analyze_audio",
]