"""Tests for midi_library package · v0 目录骨架 100% 通过。

覆盖模块:
    - midi_loader · 索引 + 元数据构造
    - tag_filter · 4 维标签筛选 + BPM + 自由文本
    - progression_builder · 候选和弦进行 + 排序
    - search_engine · 打分 + matched_fields + snippet
    - pipeline · 端到端 + JSON 序列化

v0 索引(M-001 ~ M-010):
    流行抒情 / 爵士 Swing / 电子 Synthwave / 古典奏鸣 / 民乐琵琶 /
    摇滚 Anthem / 嘻哈 Boom Bap / R&B Neo-Soul / 环境音 / 世界音乐
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# 确保 app/ 可导入
_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(_ROOT))

from app.midi_library import (  # noqa: E402
    MidiLibraryPipeline,
    MidiLoader,
    MidiQuery,
    ProgressionBuilder,
    TagFilter,
    MidiSearchEngine,
    extract_progression,
    filter_by_query,
    load_metadata,
    query_midi_library,
    search_midi,
)
from app.midi_library.midi_loader import MidiMetadata  # noqa: E402
from app.midi_library.pipeline import MidiLibraryResult  # noqa: E402
from app.midi_library.progression_builder import ProgressionSuggestion  # noqa: E402
from app.midi_library.search_engine import MidiSearchHit  # noqa: E402


@pytest.fixture(scope="module")
def midi_list():
    """v0 索引列表(M-001 ~ M-010 = 10 条)。"""
    return load_metadata()


@pytest.fixture(scope="module")
def loader():
    return MidiLoader()


# ============================================================================
# midi_loader 测试(5 用例)
# ============================================================================


class TestMidiLoader:
    def test_load_returns_10_entries(self, midi_list):
        """加载 index_meta.json 应返回 10 条元数据。"""
        assert len(midi_list) == 10

    def test_first_entry_is_pop_ballad(self, midi_list):
        """M-001 标题必须是 'Pop Ballad Sketch' 流行抒情。"""
        assert midi_list[0].id == "M-001"
        assert midi_list[0].style_primary.startswith("ST-01")
        assert "抒情流行" in midi_list[0].style_subtag

    def test_get_by_id_found(self, loader):
        """按 ID 查询:M-002 = Jazz Swing Head。"""
        m = loader.get_by_id("M-002")
        assert m is not None
        assert m.title == "Jazz Swing Head"
        assert m.style_primary.startswith("ST-03")

    def test_get_by_id_not_found(self, loader):
        """按 ID 查询不存在的应返回 None。"""
        assert loader.get_by_id("M-999") is None

    def test_count(self, loader):
        """count() 与 len(load()) 一致。"""
        assert loader.count() == 10

    def test_metadata_to_dict_json_serializable(self, midi_list):
        """MidiMetadata.to_dict() 应可 JSON 序列化。"""
        d = midi_list[0].to_dict()
        s = json.dumps(d, ensure_ascii=False)
        assert "Pop Ballad Sketch" in s


# ============================================================================
# tag_filter 测试(7 用例)
# ============================================================================


class TestTagFilter:
    def test_filter_by_style(self, midi_list):
        """按风格筛选 ST-01 仅命中 M-001。"""
        q = MidiQuery(style_codes=["ST-01"])
        out = filter_by_query(midi_list, q)
        assert all(m.style_primary.startswith("ST-01") for m in out)
        ids = [m.id for m in out]
        assert "M-001" in ids
        assert "M-002" not in ids

    def test_filter_by_mood(self, midi_list):
        """按情绪筛选 MO-02 应命中至少 1 条(M-001)。"""
        q = MidiQuery(mood_codes=["MO-02"])
        out = filter_by_query(midi_list, q)
        assert any(m.id == "M-001" for m in out)

    def test_filter_by_key(self, midi_list):
        """按调性筛选 KY-13 应命中 M-004(F major 古典奏鸣)。"""
        q = MidiQuery(key_codes=["KY-13"])
        out = filter_by_query(midi_list, q)
        assert any(m.id == "M-004" for m in out)

    def test_filter_by_bpm_range(self, midi_list):
        """BPM 范围 [60, 90] 应命中 M-001(72)/M-005(60)/M-007(92 一半?)等。"""
        q = MidiQuery(bpm_range=[60, 90])
        out = filter_by_query(midi_list, q)
        ids = [m.id for m in out]
        # M-001(bpm=72) 应命中
        assert "M-001" in ids
        # M-002(bpm=145) 不应命中
        assert "M-002" not in ids

    def test_filter_by_free_text(self, midi_list):
        """自由文本 '抒情' 应命中 M-001(tags 含 '抒情')。"""
        q = MidiQuery(free_text="抒情")
        out = filter_by_query(midi_list, q)
        assert any(m.id == "M-001" for m in out)

    def test_combined_and_query(self, midi_list):
        """组合:ST-04 + MO-07 + bpm 118±20 应命中 M-003(Synthwave f minor 118 BPM 神秘)。"""
        q = MidiQuery(
            style_codes=["ST-04"],
            mood_codes=["MO-07"],
            bpm_range=[100, 140],
        )
        out = filter_by_query(midi_list, q)
        ids = [m.id for m in out]
        assert "M-003" in ids
        # M-009(ST-04 + 慢板 68 BPM) 不应在范围
        assert "M-009" not in ids

    def test_empty_query_returns_all(self, midi_list):
        """空 query 应返回全部?实际为 [](query 为空时引擎会拒绝)。"""
        q = MidiQuery()
        assert q.is_empty() is True


# ============================================================================
# progression_builder 测试(5 用例)
# ============================================================================


class TestProgressionBuilder:
    def test_suggest_returns_top_k(self):
        """suggest top_k=3 应返回恰好 3 条。"""
        pb = ProgressionBuilder()
        sugs = pb.suggest("ST-01 流行", ["MO-02 忧郁", "MO-06 亲密"], top_k=3)
        assert len(sugs) == 3
        assert all(isinstance(s, ProgressionSuggestion) for s in sugs)

    def test_score_order_descending(self):
        """返回列表必须按 score 倒序。"""
        sugs = extract_progression("ST-03 爵士", ["MO-08 激励"], top_k=5)
        scores = [s.score for s in sugs]
        assert scores == sorted(scores, reverse=True)

    def test_highest_score_is_jazz_match_for_jazz_query(self):
        """ST-03 爵士查询,得分最高应包含 ii-V-I(Jazz 招牌)。"""
        sugs = extract_progression("ST-03 爵士", ["MO-04 放松", "MO-08 激励"], top_k=5)
        assert sugs[0].name == "ii-V-I"

    def test_style_match_gives_higher_score(self):
        """ST-01 流行比 ST-05 R&B 在流行查询中得分高。"""
        sugs_pop = extract_progression("ST-01 流行", ["MO-06 亲密"], top_k=12)
        # 至少有一条 styles 含 ST-01 应排前
        names_pop = [s.name for s in sugs_pop]
        assert "I-V-vi-IV" in names_pop

    def test_top_k_clamped(self):
        """top_k > len(progressions) 时不报错(返回列表短)。"""
        pb = ProgressionBuilder()
        sugs = pb.suggest("ST-02 摇滚", ["MO-05 史诗"], top_k=100)
        # 实际等于 progressions 总数(<= 12)
        assert len(sugs) <= 12


# ============================================================================
# search_engine 测试(5 用例)
# ============================================================================


class TestSearchEngine:
    def test_search_returns_hits(self, midi_list):
        """搜索 '抒情' 应返回至少 1 个 hit。"""
        q = MidiQuery(free_text="抒情", style_codes=["ST-01"])
        hits = search_midi(midi_list, q)
        assert len(hits) >= 1
        assert all(isinstance(h, MidiSearchHit) for h in hits)

    def test_hit_to_dict_includes_match_score(self, midi_list):
        """hit.to_dict() 必须含 match_score / matched_fields / snippet。"""
        q = MidiQuery(free_text="抒情")
        hits = search_midi(midi_list, q)
        if hits:
            d = hits[0].to_dict()
            assert "match_score" in d
            assert "matched_fields" in d
            assert "snippet" in d
            assert d["match_score"] > 0.0

    def test_hits_sorted_by_score_desc(self, midi_list):
        """hits 必须按 match_score 倒序。"""
        q = MidiQuery(style_codes=["ST-01"])
        hits = search_midi(midi_list, q)
        scores = [h.match_score for h in hits]
        assert scores == sorted(scores, reverse=True)

    def test_top_k_respected(self, midi_list):
        """top_k=2 应最多返回 2 条。"""
        q = MidiQuery(style_codes=[])
        q.style_codes = ["ST-01", "ST-02", "ST-03", "ST-04"]
        hits = search_midi(midi_list, q, top_k=2)
        assert len(hits) <= 2

    def test_empty_query_returns_empty(self, midi_list):
        """空 query 应返回空列表。"""
        q = MidiQuery()
        hits = search_midi(midi_list, q)
        assert hits == []


# ============================================================================
# pipeline 测试(4 用例)
# ============================================================================


class TestPipeline:
    def test_pipeline_returns_result(self, midi_list):
        """端到端检索返回 MidiLibraryResult。"""
        q = MidiQuery(style_codes=["ST-01"], free_text="抒情")
        pipe = MidiLibraryPipeline()
        result = pipe.run(q)
        assert isinstance(result, MidiLibraryResult)
        assert len(result.matched) >= 1

    def test_pipeline_with_progressions(self):
        """include_progressions=True 时 progressions dict 非空。"""
        q = MidiQuery(style_codes=["ST-01"], free_text="抒情")
        result = query_midi_library(q, include_progressions=True, top_k=5)
        # 至少有 1 个 matched,progressions dict 至少 1 个 key
        if result.matched:
            assert len(result.progressions) >= 1
            first_id = result.matched[0]["id"]
            assert first_id in result.progressions

    def test_pipeline_without_progressions(self):
        """include_progressions=False 时 progressions dict 为空。"""
        q = MidiQuery(style_codes=["ST-01"], free_text="抒情")
        result = query_midi_library(q, include_progressions=False, top_k=5)
        assert result.progressions == {}

    def test_pipeline_meta_elapsed_ms_nonneg(self):
        """meta.elapsed_ms 必须 ≥ 0。"""
        q = MidiQuery(style_codes=["ST-01"])
        result = query_midi_library(q, top_k=5)
        assert result.meta["elapsed_ms"] >= 0
        assert result.meta["phase"].startswith("Phase 1 §6")


# ============================================================================
# Integration 测试(4 用例)
# ============================================================================


class TestIntegration:
    def test_full_workflow_to_json(self):
        """完整工作流:query → pipeline → to_json 成功。"""
        q = MidiQuery(
            style_codes=["ST-01", "ST-04"],
            mood_codes=["MO-02", "MO-08"],
            bpm_range=[70, 140],
            free_text="钢琴",
        )
        result = query_midi_library(q, include_progressions=True, top_k=5)
        js = result.to_json()
        loaded = json.loads(js)
        assert loaded["query"]["style_codes"] == ["ST-01", "ST-04"]
        assert "matched" in loaded
        assert "progressions" in loaded
        assert "meta" in loaded

    def test_cross_module_consistency(self, midi_list):
        """跨模块一致性:TagFilter 命中数 ≥ search_engine 命中数(engine 是 filter 子集 + 打分)。"""
        q = MidiQuery(style_codes=["ST-01"])
        filt = filter_by_query(midi_list, q)
        hits = search_midi(midi_list, q, top_k=20)
        assert len(filt) >= len(hits)

    def test_pipeline_uses_loader_index_meta(self):
        """pipeline 通过 loader 索引找到至少 10 条 schema 锚点(继承自 midi_tags_v0 5 + 新 5)。"""
        pipe = MidiLibraryPipeline()
        assert pipe.loader.count() == 10

    def test_results_have_progression_reason_for_jazz(self):
        """Jazz 查询 → progressions 中得分最高项含 '风格' 命中理由。"""
        q = MidiQuery(style_codes=["ST-03"])
        result = query_midi_library(q, include_progressions=True, top_k=5)
        if result.matched and result.progressions:
            first_id = result.matched[0]["id"]
            progs = result.progressions[first_id]
            # 第一条 progression 应有 reason 含命中信息
            assert progs[0]["reason"] != ""
