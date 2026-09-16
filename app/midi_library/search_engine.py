"""MIDI 搜索引擎 · 标签筛选 + 自由文本 + 匹配打分排序。

v0 骨架:
    - 先 TagFilter 多维 AND 命中
    - 再对命中条目算 match_score(0-1)
    - score 维度:标签命中数 + 自由文本命中数 + BPM 距离
    - 按 score 倒序返回

Phase 1 续做:
    - 接 Milvus 向量相似度(余弦)做相似 MIDI 召回
    - 接用户收藏历史做个性化 rerank
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from app.midi_library.midi_loader import MidiMetadata
from app.midi_library.tag_filter import MidiQuery, TagFilter


@dataclass
class MidiSearchHit:
    """单条 MIDI 检索命中。

    Attributes:
        midi: 元数据。
        match_score: 综合匹配分 0-1(越高越相关)。
        matched_fields: 命中字段列表(如 ['mood', 'style', 'tempo'])。
        snippet: 命中片段预览(如 title + tags slice)。
    """

    midi: MidiMetadata
    match_score: float
    matched_fields: List[str]
    snippet: str

    def to_dict(self) -> Dict:
        return {
            "id": self.midi.id,
            "title": self.midi.title,
            "style_primary": self.midi.style_primary,
            "mood": list(self.midi.mood),
            "tempo": self.midi.tempo,
            "bpm": self.midi.bpm,
            "key": self.midi.key,
            "duration_sec": self.midi.duration_sec,
            "tags": list(self.midi.tags),
            "match_score": round(self.match_score, 3),
            "matched_fields": list(self.matched_fields),
            "snippet": self.snippet,
        }


class MidiSearchEngine:
    """搜索引擎 · 标签 + 自由文本 + 打分排序。"""

    def __init__(self, tag_filter: TagFilter = None) -> None:
        self.tag_filter = tag_filter or TagFilter()

    @staticmethod
    def _score_match(m: MidiMetadata, query: MidiQuery) -> float:
        """打分:标签命中数 + 自由文本命中数。

        Args:
            m: MIDI 元数据。
            query: 查询条件。

        Returns:
            0.0 ~ 1.0 分数。
        """
        score = 0.0
        # 每命中一维加 0.25,理论最高 1.0
        if query.style_codes:
            if any(m.style_primary.startswith(c) for c in query.style_codes):
                score += 0.25
        if query.mood_codes:
            for c in query.mood_codes:
                if any(em.startswith(c) for em in m.mood):
                    score += 0.25
                    break
        if query.key_codes:
            if any(m.key.startswith(c) for c in query.key_codes):
                score += 0.25
        if query.bpm_range is not None and len(query.bpm_range) == 2:
            lo, hi = query.bpm_range
            if lo <= m.bpm <= hi:
                score += 0.15
            else:
                # 距离惩罚
                dist = min(abs(m.bpm - lo), abs(m.bpm - hi))
                score += max(0.0, 0.1 - dist * 0.002)
        # 自由文本命中奖励 0.1
        if query.free_text.strip():
            text = query.free_text.lower()
            if text in m.title.lower() or any(text in t.lower() for t in m.tags):
                score += 0.1
        return min(1.0, score)

    @staticmethod
    def _matched_fields(m: MidiMetadata, query: MidiQuery) -> List[str]:
        """列出命中字段。"""
        fields: List[str] = []
        if query.style_codes and any(m.style_primary.startswith(c) for c in query.style_codes):
            fields.append("style")
        if query.mood_codes and any(em.startswith(c) for em in m.mood for c in query.mood_codes):
            fields.append("mood")
        if query.key_codes and any(m.key.startswith(c) for c in query.key_codes):
            fields.append("key")
        if query.bpm_range is not None and len(query.bpm_range) == 2:
            lo, hi = query.bpm_range
            if lo <= m.bpm <= hi:
                fields.append("tempo")
        if query.free_text.strip() and (
            query.free_text.lower() in m.title.lower()
            or any(query.free_text.lower() in t.lower() for t in m.tags)
        ):
            fields.append("text")
        return fields

    @staticmethod
    def _snippet(m: MidiMetadata, max_chars: int = 64) -> str:
        """命中片段预览。"""
        base = f"{m.title} · " + " · ".join(m.tags[:3])
        return base[:max_chars] + ("..." if len(base) > max_chars else "")

    def search(
        self, midi_list: List[MidiMetadata], query: MidiQuery, top_k: int = 20
    ) -> List[MidiSearchHit]:
        """搜索主入口:筛选 → 打分 → 取 top_k。

        Args:
            midi_list: 候选列表。
            query: 查询条件。
            top_k: 返回前 k 条。

        Returns:
            MidiSearchHit 列表。
        """
        if query.is_empty():
            return []
        candidates = self.tag_filter.filter(midi_list, query)
        hits: List[MidiSearchHit] = []
        for m in candidates:
            score = self._score_match(m, query)
            fields = self._matched_fields(m, query)
            hits.append(
                MidiSearchHit(
                    midi=m,
                    match_score=score,
                    matched_fields=fields,
                    snippet=self._snippet(m),
                )
            )
        hits.sort(key=lambda h: h.match_score, reverse=True)
        return hits[:top_k]


def search_midi(
    midi_list: List[MidiMetadata], query: MidiQuery, top_k: int = 20
) -> List[MidiSearchHit]:
    """便捷函数:搜索 MIDI。"""
    return MidiSearchEngine().search(midi_list, query, top_k)
