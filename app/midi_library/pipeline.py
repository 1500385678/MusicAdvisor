"""MIDI 素材库端到端流水线 · query → 命中 + 候选和弦进行 → JSON。

v0 骨架:
    - 串行编排 midi_loader → tag_filter → search_engine → progression_builder
    - 返回结构化 MidiLibraryResult(JSON 可序列化)
    - 端到端 metrics(elapsed_ms + matched count)

Phase 1 续做:
    - 并行化多索引查询 + Milvus 向量召回
    - 缓存层(LRU)
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from typing import Dict, List

from app.midi_library.midi_loader import MidiLoader, load_metadata
from app.midi_library.progression_builder import ProgressionBuilder, extract_progression
from app.midi_library.search_engine import MidiSearchEngine, MidiSearchHit
from app.midi_library.tag_filter import MidiQuery


@dataclass
class MidiLibraryResult:
    """MIDI 检索完整结果(JSON 可序列化)。

    Attributes:
        query: 查询条件 echo。
        matched: 命中 MIDI 列表。
        progressions: 每个命中 MIDI 的候选和弦进行(1:M)。
        meta: 元数据(版本/时间戳/耗时)。
    """

    query: Dict
    matched: List[Dict]
    progressions: Dict[str, List[Dict]]  # midi_id -> progressions
    meta: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


class MidiLibraryPipeline:
    """端到端 MIDI 素材库检索流水线。"""

    def __init__(
        self,
        loader: MidiLoader = None,
        search_engine: MidiSearchEngine = None,
        progression_builder: ProgressionBuilder = None,
    ) -> None:
        """初始化流水线(参数注入便于测试)。"""
        self.loader = loader or MidiLoader()
        self.search_engine = search_engine or MidiSearchEngine()
        self.progression_builder = progression_builder or ProgressionBuilder()

    def run(
        self,
        query: MidiQuery,
        include_progressions: bool = True,
        top_k: int = 20,
    ) -> MidiLibraryResult:
        """执行端到端检索。

        Args:
            query: 查询条件。
            include_progressions: 是否对每个命中 MIDI 提取候选和弦进行。
            top_k: 最大返回命中数。

        Returns:
            MidiLibraryResult(含耗时 + matched + progressions)。
        """
        t0 = time.perf_counter()
        # 1) 加载元数据索引
        midi_list = self.loader.load()
        # 2) 搜索引擎做标签筛选 + 打分
        hits: List[MidiSearchHit] = self.search_engine.search(
            midi_list, query, top_k=top_k
        )
        matched_dicts = [h.to_dict() for h in hits]
        # 3) 可选:为每个 MIDI 提取候选和弦进行
        prog_map: Dict[str, List[Dict]] = {}
        if include_progressions:
            for h in hits:
                m = h.midi
                sugs = extract_progression(m.style_primary, list(m.mood), top_k=3)
                prog_map[m.id] = [s.to_dict() for s in sugs]
        elapsed_ms = int((time.perf_counter() - t0) * 1000)
        meta = {
            "version": "0.1.0",
            "phase": "Phase 1 §6 第 4 项 v0 目录骨架",
            "schema_source": "analysis_demo/scores/midi_tags_v0.json",
            "indexed_count": len(midi_list),
            "matched_count": len(hits),
            "elapsed_ms": elapsed_ms,
        }
        return MidiLibraryResult(
            query=query.to_dict(),
            matched=matched_dicts,
            progressions=prog_map,
            meta=meta,
        )


def query_midi_library(
    query: MidiQuery,
    include_progressions: bool = True,
    top_k: int = 20,
) -> MidiLibraryResult:
    """便捷函数:端到端检索。"""
    return MidiLibraryPipeline().run(
        query, include_progressions=include_progressions, top_k=top_k
    )
