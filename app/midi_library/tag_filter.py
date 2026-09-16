"""标签筛选器 · 按 BPM/调性/情绪/风格 4 维筛选 MIDI。

v0 骨架实现:
    - 多维标签 AND 匹配(任一维度不命中即剔除)
    - BPM 范围兜底(数值 ± 20 容差)
    - 自由文本模糊匹配 title + tags
    - Phase 1 续做接 Milvus 向量相似度

契约源:`analysis_demo/scores/midi_tags_v0.json` v0 4 维标签字典
    (ST-XX 16 / MO-XX 8 / TP-XX 5 / KY-XX 24)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from app.midi_library.midi_loader import MidiMetadata


@dataclass
class MidiQuery:
    """MIDI 检索条件。

    Attributes:
        style_codes: 风格 ST-XX 列表(空 = 不过滤)。
        mood_codes: 情绪 MO-XX 列表(空 = 不过滤)。
        key_codes: 调性 KY-XX 列表(空 = 不过滤)。
        bpm_range: BPM 范围 [min, max];None = 不过滤。
        free_text: 自由文本关键词(模糊匹配 title + tags)。
    """

    style_codes: List[str] = field(default_factory=list)
    mood_codes: List[str] = field(default_factory=list)
    key_codes: List[str] = field(default_factory=list)
    bpm_range: Optional[List[int]] = None
    free_text: str = ""

    def is_empty(self) -> bool:
        """判断 query 是否为空(任一维度有值即非空)。"""
        if self.style_codes or self.mood_codes or self.key_codes:
            return False
        if self.bpm_range is not None:
            return False
        if self.free_text.strip():
            return False
        return True

    def to_dict(self) -> dict:
        """转字典(JSON 友好)。"""
        return {
            "style_codes": list(self.style_codes),
            "mood_codes": list(self.mood_codes),
            "key_codes": list(self.key_codes),
            "bpm_range": list(self.bpm_range) if self.bpm_range else None,
            "free_text": self.free_text,
        }


class TagFilter:
    """标签筛选器 · 4 维 AND 匹配。"""

    @staticmethod
    def _has_any_code(haystack_list: List[str], codes: List[str]) -> bool:
        """判断 haystack_list 中是否至少包含 codes 任一前缀(如 'MO-02')。

        Args:
            haystack_list: haystack 元数据列表(如 mood=['MO-02 忧郁', ...])。
            codes: 检索 ID 前缀列表(如 ['MO-02', 'MO-06'])。

        Returns:
            bool:haystack 中任一项以任一 code 开头即 True。
        """
        if not codes:
            return True
        for item in haystack_list:
            for code in codes:
                if item.startswith(code):
                    return True
        return False

    @staticmethod
    def _match_bpm(bpm: int, bpm_range: Optional[List[int]]) -> bool:
        """BPM 范围匹配。

        Args:
            bpm: 实际 BPM。
            bpm_range: [min, max] 范围;None = 不过滤。
        """
        if bpm_range is None or len(bpm_range) != 2:
            return True
        lo, hi = bpm_range
        return lo <= bpm <= hi

    @staticmethod
    def _match_text(m: MidiMetadata, text: str) -> bool:
        """自由文本模糊匹配 title + tags。"""
        if not text.strip():
            return True
        text_lower = text.lower()
        if text_lower in m.title.lower():
            return True
        for tag in m.tags:
            if text_lower in tag.lower():
                return True
        return False

    def filter(
        self, midi_list: List[MidiMetadata], query: MidiQuery
    ) -> List[MidiMetadata]:
        """按 query 4 维筛选。

        Args:
            midi_list: 候选 MIDI 元数据列表。
            query: 查询条件。

        Returns:
            命中的 MIDI 列表(保持原顺序)。
        """
        out: List[MidiMetadata] = []
        for m in midi_list:
            # 风格(mood 字段命名沿用 midi_tags_v0 实际字段名,style 在 style_primary/subtag)
            if not self._has_any_code([m.style_primary], query.style_codes):
                continue
            # 情绪
            if not self._has_any_code(list(m.mood), query.mood_codes):
                continue
            # 调性
            if not self._has_any_code([m.key], query.key_codes):
                continue
            # BPM
            if not self._match_bpm(m.bpm, query.bpm_range):
                continue
            # 自由文本
            if not self._match_text(m, query.free_text):
                continue
            out.append(m)
        return out


def filter_by_query(
    midi_list: List[MidiMetadata], query: MidiQuery
) -> List[MidiMetadata]:
    """便捷函数:按 query 4 维筛选。"""
    return TagFilter().filter(midi_list, query)
