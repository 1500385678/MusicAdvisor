"""和弦进行建议器测试 v0

8 用例覆盖:
- chord_progressions: 情绪匹配 + 候选数限制 + 大小调区分
- emotion_keyword: 中英文匹配 + 关键词清单
- key_normalize: 24 调归一 + 等音 + 关系调
- audio_playback: JS 字符串完整性
"""
from __future__ import annotations
import sys
import os

# 把仓库根加进 sys.path 以便 `from app.chord_suggester import ...`
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from app.chord_suggester import (
    suggest_progressions,
    PROGRESSIONS_LIBRARY,
    EmotionMapper,
    KeyNormalizer,
    audio_playback_js,
    SUPPORTED_KEYS,
)


# ──────────────────────────────────────────────
# chord_progressions 测试
# ──────────────────────────────────────────────
def test_suggest_progressions_happy_returns_top_match():
    """happy 情绪返回权重最高的 I-V-vi-IV"""
    result = suggest_progressions("C", "happy", n=5)
    assert len(result) == 5
    assert result[0]["id"] == "I-V-vi-IV"
    assert result[0]["emotion_score"] >= 0.9


def test_suggest_progressions_sad_returns_top_match():
    """sad 情绪返回权重最高的 i-iv-V-i"""
    result = suggest_progressions("Am", "sad", n=5)
    assert len(result) == 5
    # 自然小调进行权重最高(sad = 1.0)
    top_ids = [r["id"] for r in result]
    assert "i-iv-V-i" in top_ids[:2]


def test_suggest_progressions_minor_returns_minor_romans():
    """小调输入返回小调 Roman Numeral"""
    result = suggest_progressions("Am", "calm", n=5)
    for c in result:
        # 小调应该用 i 而不是 I
        # 至少第一个 chord 应该是小写
        assert any(r.islower() for r in c["roman"]), f"{c['id']} should have minor roman"


def test_suggest_progressions_n_bounds():
    """n 必须 5-8"""
    try:
        suggest_progressions("C", "happy", n=4)
        assert False, "should raise"
    except ValueError:
        pass
    try:
        suggest_progressions("C", "happy", n=9)
        assert False, "should raise"
    except ValueError:
        pass
    # 边界 5 和 8 应该 OK
    assert len(suggest_progressions("C", "happy", n=5)) == 5
    assert len(suggest_progressions("C", "happy", n=8)) == 8


def test_suggest_progressions_invalid_emotion():
    """无效 emotion 应抛 ValueError"""
    try:
        suggest_progressions("C", "excited", n=5)
        assert False, "should raise"
    except ValueError:
        pass


def test_progressions_library_size():
    """进行库至少 12 项(契约 12,Phase 1 v1 扩 30+)"""
    assert len(PROGRESSIONS_LIBRARY) >= 12


# ──────────────────────────────────────────────
# emotion_keyword 测试
# ──────────────────────────────────────────────
def test_emotion_mapper_chinese_match():
    """中文关键词匹配"""
    mapper = EmotionMapper()
    assert mapper.match("快乐的早晨")[0] == "happy"
    assert mapper.match("忧伤的小调")[0] == "sad"
    assert mapper.match("史诗级电影")[0] == "epic"


def test_emotion_mapper_english_match():
    """英文关键词匹配(大小写不敏感)"""
    mapper = EmotionMapper()
    assert mapper.match("HAPPY day")[0] == "happy"
    assert mapper.match("epic movie")[0] == "epic"


def test_emotion_mapper_no_match():
    """无匹配返回 (None, 0.0)"""
    mapper = EmotionMapper()
    emo, conf = mapper.match("xyz123 random text")
    assert emo is None
    assert conf == 0.0


def test_emotion_mapper_list_keywords():
    """list_keywords 返回 zh + en 完整列表"""
    mapper = EmotionMapper()
    kws = mapper.list_keywords("jazzy")
    assert "jazzy" in kws
    assert "爵士" in kws


# ──────────────────────────────────────────────
# key_normalize 测试
# ──────────────────────────────────────────────
def test_key_normalize_basic():
    """24 调基础归一"""
    n = KeyNormalizer()
    assert n.normalize("C") == "C"
    assert n.normalize("Am") == "Am"
    assert n.normalize("F#") == "F#"
    assert n.normalize("C#m") == "C#m"


def test_key_normalize_with_suffix():
    """带后缀的调性名归一"""
    n = KeyNormalizer()
    assert n.normalize("C major") == "C"
    assert n.normalize("A minor") == "Am"
    assert n.normalize("F# major") == "F#"
    assert n.normalize("Bb major") == "A#"  # 等音归一


def test_key_normalize_chinese():
    """中文后缀归一"""
    n = KeyNormalizer()
    assert n.normalize("C大调") == "C"
    assert n.normalize("A小调") == "Am"
    assert n.normalize("Bb大调") == "A#"


def test_key_normalize_invalid():
    """无效输入抛 ValueError"""
    n = KeyNormalizer()
    try:
        n.normalize("H")  # 非法音名
        assert False, "should raise"
    except ValueError:
        pass
    try:
        n.normalize("")  # 空字符串
        assert False, "should raise"
    except ValueError:
        pass


def test_key_normalize_relative():
    """关系调转换 C ↔ Am, Am ↔ C"""
    n = KeyNormalizer()
    assert n.relative_key("C") == "Am"
    assert n.relative_key("Am") == "C"
    assert n.relative_key("G") == "Em"
    assert n.relative_key("F#") == "D#m"


def test_supported_keys_count():
    """SUPPORTED_KEYS 应该是 24"""
    assert len(SUPPORTED_KEYS) == 24


# ──────────────────────────────────────────────
# audio_playback 测试
# ──────────────────────────────────────────────
def test_audio_playback_js_string():
    """JS 源码字符串完整性"""
    js = audio_playback_js()
    assert len(js) > 500
    assert "function playProgression" in js
    assert "Tone" in js
    assert "PolySynth" in js
    # 必须覆盖所有 7 个罗马数字级别
    for degree in ["I", "II", "III", "IV", "V", "VI", "VII"]:
        assert degree in js, f"missing degree {degree}"


# ──────────────────────────────────────────────
# 跑测试
# ──────────────────────────────────────────────
if __name__ == "__main__":
    # 直接跑作为烟囱
    test_funcs = [v for k, v in globals().items() if k.startswith("test_")]
    passed, failed = 0, 0
    for fn in test_funcs:
        try:
            fn()
            print(f"  ✅ {fn.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  ❌ {fn.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"  ❌ {fn.__name__}: {type(e).__name__}: {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed, {passed + failed} total")