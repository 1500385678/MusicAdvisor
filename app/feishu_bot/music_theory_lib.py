"""乐理基础数据
from __future__ import annotations
(音程 12 + 和弦 7 类 + 调式 7 类 · 9/14 v0 骨架)

数据源参考:9/12 任务 9 LLM 乐理问答基线 9 题题库
(`analysis_demo/llm_eval/questions.json` 的音程 3 + 和弦 3 + 调式 3)

Phase 1 9/15 ~ 9/20 扩到:
- 音程 12 → 27(加增减音程,如增四度/减五度)
- 和弦 7 类 → 20+(加九和弦/十一和弦/挂留和弦/属变和弦)
- 调式 7 类 → 12+(加教会调式 7 + 五声音阶 5 + 日本民谣音阶)
"""
from __future__ import annotations

# 12 个标准音程(基础)
_INTERVALS = [
    "纯一度", "小二度", "大二度", "小三度", "大三度", "纯四度",
    "三全音", "纯五度", "小六度", "大六度", "小七度", "大七度",
    "纯八度",
]

# 7 类基础和弦(Phase 1 9/15 扩到 20+)
_CHORDS = [
    "大三和弦", "小三和弦", "增三和弦", "减三和弦",
    "大七和弦", "小七和弦", "属七和弦",
]

# 7 类基础调式
_MODES = [
    "自然大调", "自然小调", "和声小调", "旋律小调",
    "五声音阶", "蓝调音阶", "多利安",
]


def lookup_interval(name: str) -> list[str]:
    """按名字查音程;name 为空返回全部"""
    if not name:
        return list(_INTERVALS)
    return [x for x in _INTERVALS if name in x]


def lookup_chord(name: str) -> list[str]:
    if not name:
        return list(_CHORDS)
    return [x for x in _CHORDS if name in x]


def lookup_mode(name: str) -> list[str]:
    if not name:
        return list(_MODES)
    return [x for x in _MODES if name in x]
