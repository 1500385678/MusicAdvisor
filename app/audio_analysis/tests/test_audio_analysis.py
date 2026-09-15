"""Tests for audio_analysis package · v0 目录骨架 100% 通过。

覆盖模块:
    - audio_loader · 加载 + 格式校验
    - tempo_detector · BPM + 拍点 + 档位分类
    - key_detector · 调性 + 等音归一 + 24 调列表
    - chord_detector · 时间线 + 词汇表
    - visualizer · PNG 字节流
    - pipeline · 端到端 + JSON 序列化
"""

from __future__ import annotations

import base64
import json
import os
import sys
import tempfile
from pathlib import Path

import numpy as np
import pytest

# 确保 app/ 可导入
_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(_ROOT))

from app.audio_analysis import (  # noqa: E402
    AudioAnalysisPipeline,
    analyze_audio,
)
from app.audio_analysis.audio_loader import AudioData, AudioLoader, load_audio  # noqa: E402
from app.audio_analysis.chord_detector import (  # noqa: E402
    ChordDetector,
    ChordResult,
    ChordSegment,
    detect_chords,
)
from app.audio_analysis.key_detector import KeyDetector, KeyResult, detect_key  # noqa: E402
from app.audio_analysis.pipeline import AnalysisReport  # noqa: E402
from app.audio_analysis.tempo_detector import TempoDetector, detect_tempo  # noqa: E402
from app.audio_analysis.visualizer import AudioVisualizer, visualize_analysis  # noqa: E402


# ============================================================================
# audio_loader 测试
# ============================================================================


class TestAudioLoader:
    """AudioLoader 单元测试。"""

    def test_init_default(self):
        """默认 22050Hz 单声道。"""
        loader = AudioLoader()
        assert loader.target_sr == 22050
        assert loader.mono is True

    def test_init_custom(self):
        """自定义参数。"""
        loader = AudioLoader(target_sr=44100, mono=False)
        assert loader.target_sr == 44100
        assert loader.mono is False

    def test_supported_formats(self):
        """支持格式列表。"""
        loader = AudioLoader()
        assert ".mp3" in loader.SUPPORTED_FORMATS
        assert ".wav" in loader.SUPPORTED_FORMATS

    def test_load_file_not_found(self):
        """文件不存在抛错。"""
        loader = AudioLoader()
        with pytest.raises(FileNotFoundError):
            loader.load("/nonexistent/path.mp3")

    def test_load_unsupported_format(self, tmp_path):
        """不支持格式抛错。"""
        loader = AudioLoader()
        bad = tmp_path / "test.xyz"
        bad.write_bytes(b"dummy")
        with pytest.raises(ValueError, match="不支持的音频格式"):
            loader.load(bad)

    def test_load_mock_returns_audio_data(self, tmp_path):
        """加载返回 AudioData 实例。"""
        loader = AudioLoader()
        mp3 = tmp_path / "test.mp3"
        mp3.write_bytes(b"\xff\xfb\x90\x00" + b"\x00" * 100)  # fake MP3 header
        audio = loader.load(mp3)
        assert isinstance(audio, AudioData)
        assert audio.sample_rate == 22050
        assert audio.duration_sec >= 0
        assert audio.source_path.endswith("test.mp3")

    def test_load_audio_convenience(self, tmp_path):
        """便捷函数 load_audio 工作。"""
        mp3 = tmp_path / "song.mp3"
        mp3.write_bytes(b"\x00" * 50)
        audio = load_audio(mp3)
        assert isinstance(audio, AudioData)


# ============================================================================
# tempo_detector 测试
# ============================================================================


class TestTempoDetector:
    """TempoDetector 单元测试。"""

    def _make_audio(self, duration=4.0, sr=22050) -> AudioData:
        waveform = np.zeros(int(duration * sr), dtype=np.float32)
        return AudioData(
            waveform=waveform,
            sample_rate=sr,
            duration_sec=duration,
            source_path="<mock>",
        )

    def test_init_default(self):
        det = TempoDetector()
        assert det.hop_length == 512

    def test_detect_returns_result(self):
        det = TempoDetector()
        audio = self._make_audio()
        result = det.detect(audio)
        assert isinstance(result.bpm, float)
        assert result.bpm > 0
        assert isinstance(result.beat_times, list)
        assert result.confidence >= 0

    def test_bpm_buckets(self):
        """档位分类。"""
        assert TempoDetector.classify_bpm(70) == "slow/ballad"
        assert TempoDetector.classify_bpm(90) == "moderate"
        assert TempoDetector.classify_bpm(110) == "medium"
        assert TempoDetector.classify_bpm(130) == "uptempo"
        assert TempoDetector.classify_bpm(160) == "fast"
        assert TempoDetector.classify_bpm(200) == "very_fast"
        assert TempoDetector.classify_bpm(250) == "extreme"

    def test_detect_tempo_convenience(self):
        audio = self._make_audio()
        result = detect_tempo(audio)
        assert result.bpm > 0


# ============================================================================
# key_detector 测试
# ============================================================================


class TestKeyDetector:
    """KeyDetector 单元测试。"""

    def _make_audio(self) -> AudioData:
        waveform = np.zeros(22050, dtype=np.float32)
        return AudioData(waveform, 22050, 1.0, "<mock>")

    def test_24_keys_count(self):
        """24 调(12 大 + 12 小)。"""
        keys = KeyDetector.all_keys()
        assert len(keys) == 24
        # 大小调各 12 个
        majors = [k for k in keys if not k.endswith("m")]
        minors = [k for k in keys if k.endswith("m")]
        assert len(majors) == 12
        assert len(minors) == 12

    def test_detect_returns_result(self):
        det = KeyDetector()
        audio = self._make_audio()
        result = det.detect(audio)
        assert isinstance(result.key, str)
        assert result.scale in ("major", "minor")
        assert 0 <= result.confidence <= 1
        assert result.chroma.shape == (12,)

    def test_normalize_key_flat_to_sharp(self):
        """等音归一 flat → sharp。"""
        assert KeyDetector.normalize_key("Db") == "C#"
        assert KeyDetector.normalize_key("Eb") == "D#"
        assert KeyDetector.normalize_key("Gb") == "F#"
        assert KeyDetector.normalize_key("Ab") == "G#"
        assert KeyDetector.normalize_key("Bb") == "A#"

    def test_normalize_key_already_sharp(self):
        """已经是 sharp 不变。"""
        assert KeyDetector.normalize_key("C#") == "C#"
        assert KeyDetector.normalize_key("F#") == "F#"

    def test_top_k_candidates(self):
        """Top-K 候选。"""
        det = KeyDetector(top_k=3)
        audio = self._make_audio()
        result = det.detect(audio)
        assert len(result.candidates) <= 3

    def test_detect_key_convenience(self):
        audio = self._make_audio()
        result = detect_key(audio)
        assert result.scale in ("major", "minor")


# ============================================================================
# chord_detector 测试
# ============================================================================


class TestChordDetector:
    """ChordDetector 单元测试。"""

    def _make_audio(self, duration=8.0) -> AudioData:
        waveform = np.zeros(int(duration * 22050), dtype=np.float32)
        return AudioData(waveform, 22050, duration, "<mock>")

    def test_detect_returns_segments(self):
        det = ChordDetector()
        audio = self._make_audio()
        result = det.detect(audio)
        assert len(result.segments) >= 1
        for seg in result.segments:
            assert seg.start_time >= 0
            assert seg.end_time > seg.start_time
            assert seg.duration() > 0
            assert seg.confidence >= 0

    def test_segments_cover_duration(self):
        """片段覆盖完整时长。"""
        det = ChordDetector()
        audio = self._make_audio(duration=8.0)
        result = det.detect(audio)
        assert abs(result.segments[-1].end_time - 8.0) < 0.5

    def test_vocabulary_unique(self):
        """词汇表去重。"""
        det = ChordDetector()
        audio = self._make_audio()
        result = det.detect(audio)
        assert len(result.vocabulary) == result.unique_count
        assert len(set(result.vocabulary)) == len(result.vocabulary)

    def test_chord_segment_duration(self):
        """ChordSegment.duration 计算。"""
        seg = ChordSegment(0.0, 2.5, "C", 0.9)
        assert seg.duration() == 2.5

    def test_detect_chords_convenience(self):
        audio = self._make_audio()
        result = detect_chords(audio)
        assert len(result.segments) >= 1


# ============================================================================
# visualizer 测试
# ============================================================================


class TestVisualizer:
    """AudioVisualizer 单元测试。"""

    def _make_full_input(self):
        waveform = np.zeros(22050 * 4, dtype=np.float32)
        audio = AudioData(waveform, 22050, 4.0, "<mock>")
        tempo = TempoDetector().detect(audio)
        key = KeyDetector().detect(audio)
        chords = ChordDetector().detect(audio)
        return audio, tempo, key, chords

    def test_render_returns_png_bytes(self):
        viz = AudioVisualizer()
        audio, tempo, key, chords = self._make_full_input()
        result = viz.render(audio, tempo, key, chords)
        assert isinstance(result.image_bytes, bytes)
        # PNG magic header
        assert result.image_bytes.startswith(b"\x89PNG")
        assert result.width > 0
        assert result.height > 0
        assert result.panels >= 1

    def test_render_custom_size(self):
        viz = AudioVisualizer(width=1600, height=900)
        audio, tempo, key, chords = self._make_full_input()
        result = viz.render(audio, tempo, key, chords)
        assert result.width == 1600
        assert result.height == 900

    def test_visualize_analysis_convenience(self):
        audio, tempo, key, chords = self._make_full_input()
        result = visualize_analysis(audio, tempo, key, chords)
        assert result.image_bytes.startswith(b"\x89PNG")


# ============================================================================
# pipeline 测试
# ============================================================================


class TestPipeline:
    """AudioAnalysisPipeline 端到端测试。"""

    def _create_fake_audio(self, tmp_path, ext=".mp3", duration_sec=4) -> Path:
        """创建 fake 音频文件用于流水线测试。"""
        p = tmp_path / f"test{ext}"
        p.write_bytes(b"\xff\xfb\x90\x00" + b"\x00" * 200)
        return p

    def test_pipeline_init(self):
        pipeline = AudioAnalysisPipeline()
        assert pipeline.loader is not None
        assert pipeline.tempo_detector is not None
        assert pipeline.key_detector is not None
        assert pipeline.chord_detector is not None
        assert pipeline.visualizer is not None

    def test_analyze_returns_report(self, tmp_path):
        audio_file = self._create_fake_audio(tmp_path, duration_sec=4)
        pipeline = AudioAnalysisPipeline()
        report = pipeline.analyze(str(audio_file))
        assert isinstance(report, AnalysisReport)
        assert report.source_path.endswith(".mp3")
        assert report.duration_sec > 0
        assert "bpm" in report.tempo
        assert "key" in report.key
        assert "segments" in report.chords
        assert report.visualization_png_b64  # 非空 Base64

    def test_report_to_json_serializable(self, tmp_path):
        """JSON 序列化无 numpy 残留。"""
        audio_file = self._create_fake_audio(tmp_path)
        pipeline = AudioAnalysisPipeline()
        report = pipeline.analyze(str(audio_file))
        s = report.to_json()
        parsed = json.loads(s)
        assert isinstance(parsed, dict)
        assert "tempo" in parsed
        assert "key" in parsed
        # chroma 应已转 list
        assert isinstance(parsed["key"]["chroma"], list)
        # PNG Base64 解码回字节流
        png_bytes = base64.b64decode(parsed["visualization_png_b64"])
        assert png_bytes.startswith(b"\x89PNG")

    def test_analyze_audio_convenience(self, tmp_path):
        audio_file = self._create_fake_audio(tmp_path)
        report = analyze_audio(str(audio_file))
        assert isinstance(report, AnalysisReport)


# ============================================================================
# 集成测试
# ============================================================================


class TestIntegration:
    """模块间集成测试。"""

    def test_full_chain_consistency(self, tmp_path):
        """端到端:loader → tempo → key → chord → viz → report 一致性。"""
        audio_file = tmp_path / "chain.mp3"
        audio_file.write_bytes(b"\x00" * 150)
        report = analyze_audio(str(audio_file))
        # 4 块都有数据
        assert report.tempo["bpm"] > 0
        assert report.tempo["bpm_bucket"] in [
            "slow/ballad",
            "moderate",
            "medium",
            "uptempo",
            "fast",
            "very_fast",
            "extreme",
        ]
        assert report.key["scale"] in ("major", "minor")
        assert len(report.chords["segments"]) >= 1
        # meta 三置信度存在
        assert "tempo_confidence" in report.meta
        assert "key_confidence" in report.meta
        assert "mean_chord_confidence" in report.meta


if __name__ == "__main__":
    pytest.main([__file__, "-v"])