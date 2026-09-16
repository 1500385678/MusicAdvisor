"""和弦进行提取 · MIDI 音符 → 候选和弦进行。

v0 骨架实现(无 .mid 二进制依赖):
    - 接受 MidiMetadata + 可选 note 序列(框架测试用)→ 返回 4-8 套候选和弦进行
    - 基于元数据 `style_primary` + `key` + `bpm` 启发式生成,Phase 1 真实模式
      接 pretty_midi 读音高 → chroma → Krumhansl-Schmuckler / 168 模板匹配
    - 复用 §6 第 2 项 chord_suggester 的 12 经典进行模板数据流(契约)

设计要点:
    - 不绑死 MIDI 真文件,与 chord_suggester 解耦(后者亦 v0 骨架)
    - 让本包独立测试 + 端到端 pipeline 跑通
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List


# 12 经典进行(沿用 chord_suggester.chord_progressions v0 数据流契约)
# Phase 1 真实模式时改为 import chord_suggester.chord_progressions
_BUILTIN_PROGRESSIONS: List[Dict] = [
    {"name": "I-V-vi-IV", "emotions": ["MO-04 放松", "MO-06 亲密"], "styles": ["ST-01"]},
    {"name": "vi-IV-I-V", "emotions": ["MO-02 忧郁", "MO-06 亲密"], "styles": ["ST-01"]},
    {"name": "I-IV-V-I", "emotions": ["MO-08 激励"], "styles": ["ST-01", "ST-02"]},
    {"name": "ii-V-I", "emotions": ["MO-04 放松", "MO-08 激励"], "styles": ["ST-03"]},
    {"name": "I-vi-ii-V", "emotions": ["MO-01 欢快"], "styles": ["ST-04"]},
    {"name": "I-VII-IV-I", "emotions": ["MO-04 放松"], "styles": ["ST-04"]},
    {"name": "I-vi-IV-V", "emotions": ["MO-06 亲密"], "styles": ["ST-05"]},
    {"name": "bVI-bIII-bVII-I", "emotions": ["MO-07 神秘"], "styles": ["ST-04", "ST-06"]},
    {"name": "12-bar Blues", "emotions": ["MO-04 放松", "MO-08 激励"], "styles": ["ST-02", "ST-03"]},
    {"name": "Andalusian (i-VII-VI-V)", "emotions": ["MO-02 忧郁"], "styles": ["ST-02", "ST-15"]},
    {"name": "Pachelbel Canon (I-V-vi-iii-IV)", "emotions": ["MO-01 欢快", "MO-06 亲密"], "styles": ["ST-01"]},
    {"name": "I-vi-IV-V (50s progression)", "emotions": ["MO-06 亲密"], "styles": ["ST-01"]},
]


_STYLE_CODE_RE = re.compile(r"(ST-\d{2})")


def _style_code(style_primary: str) -> str:
    """从 `style_primary`(如 'ST-01 流行')抽取 ST-XX。"""
    m = _STYLE_CODE_RE.search(style_primary)
    return m.group(1) if m else ""


@dataclass
class ProgressionSuggestion:
    """和弦进行建议。

    Attributes:
        name: 进行名称(如 'I-V-vi-IV')。
        score: 匹配分数 0-1。
        reason: 匹配理由。
    """

    name: str
    score: float
    reason: str = ""

    def to_dict(self) -> Dict:
        return {"name": self.name, "score": round(self.score, 3), "reason": self.reason}


class ProgressionBuilder:
    """和弦进行提取器(v0 骨架:启发式匹配)。"""

    def __init__(self) -> None:
        self.progressions = list(_BUILTIN_PROGRESSIONS)

    def suggest(
        self, style_primary: str, mood_list: List[str], top_k: int = 5
    ) -> List[ProgressionSuggestion]:
        """基于风格 + 情绪,返回候选和弦进行 top_k。

        Args:
            style_primary: 'ST-XX 中文名'(如 'ST-01 流行')。
            mood_list: 情绪列表(如 ['MO-02 忧郁', 'MO-06 亲密'])。
            top_k: 返回前 k 条。

        Returns:
            ProgressionSuggestion 列表(按分数倒序)。
        """
        target_style = _style_code(style_primary)
        scored: List[ProgressionSuggestion] = []
        for prog in self.progressions:
            score = 0.0
            reasons: List[str] = []
            # 风格匹配
            if target_style and target_style in prog.get("styles", []):
                score += 0.6
                reasons.append(f"风格 {target_style} 命中")
            # 情绪匹配
            mood_hit = 0
            for m_emotion in prog.get("emotions", []):
                for qm in mood_list:
                    if qm.startswith(m_emotion.split()[0]) or m_emotion.startswith(qm.split()[0]):
                        mood_hit += 1
            if mood_hit > 0:
                score += min(0.4, mood_hit * 0.2)
                reasons.append(f"情绪命中 {mood_hit} 项")
            scored.append(
                ProgressionSuggestion(
                    name=prog["name"],
                    score=score,
                    reason=" + ".join(reasons) if reasons else "通用模板",
                )
            )
        scored.sort(key=lambda p: p.score, reverse=True)
        return scored[:top_k]


def extract_progression(
    style_primary: str, mood_list: List[str], top_k: int = 5
) -> List[ProgressionSuggestion]:
    """便捷函数:返回和弦进行候选。"""
    return ProgressionBuilder().suggest(style_primary, mood_list, top_k)
