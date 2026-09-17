"""MIDI 素材库最小版 package.

Phase 1 §6 第 4 项 · 标签筛选(MIDI 元数据 → 候选 MIDI),内置 5 起步 → 1 万目标。

本包为 v0 目录骨架,接口稳定但部分算法为占位实现;Phase 1 续做替换为
mido / pretty_midi 真链路 + Milvus 向量检索(参见 analysis_demo/midi_tags_v0.json
契约),与 §6 第 1 + 2 + 3 项(feishu_bot / chord_suggester / audio_analysis)同模式。

设计要点:
    - 标签字典契约沿用 analysis_demo/scores/midi_tags_v0.json:ST(风格 16)/
      MO(情绪 8)/TP(BPM 5)/KY(调性 24)
    - 索引元数据挂本包 index_meta.json(M-001 ~ M-010),Phase 1 续做扩到 1 万条
    - 流程:MIDI 加载(midi_loader)→ 标签筛选(tag_filter)→
      自由文本(score)/ 排序 → 搜索(search_engine)→ 编排(pipeline)
"""

from app.midi_library.midi_loader import MidiLoader, MidiMetadata, load_metadata
from app.midi_library.tag_filter import TagFilter, MidiQuery, filter_by_query
from app.midi_library.progression_builder import (
    ProgressionBuilder,
    extract_progression,
)
from app.midi_library.search_engine import MidiSearchEngine, search_midi
from app.midi_library.pipeline import MidiLibraryPipeline, query_midi_library
from app.midi_library.batch_loader import (
    BatchValidationError,
    BatchValidationReport,
    append_batch,
    load_batch_json,
    next_id,
    validate_batch,
    validate_entry,
)

__version__ = "0.1.0"
__phase__ = "Phase 1 §6 第 4 项 v0 + 续做批量入库脚手架 v0"
__schema_source__ = "analysis_demo/scores/midi_tags_v0.json v0 4 维标签字典"

__all__ = [
    # MIDI 加载与元数据
    "MidiLoader",
    "MidiMetadata",
    "load_metadata",
    # 标签筛选
    "TagFilter",
    "MidiQuery",
    "filter_by_query",
    # 和弦进行提取
    "ProgressionBuilder",
    "extract_progression",
    # 搜索引擎
    "MidiSearchEngine",
    "search_midi",
    # 端到端流水线
    "MidiLibraryPipeline",
    "query_midi_library",
    # 批量入库脚手架(9/18 续做)
    "BatchValidationError",
    "BatchValidationReport",
    "validate_entry",
    "validate_batch",
    "append_batch",
    "load_batch_json",
    "next_id",
]
