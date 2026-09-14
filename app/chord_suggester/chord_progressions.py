"""和弦进行模板库 + 候选算法

设计:
- 12 种经典 4 小节和弦进行(I-V-vi-IV / ii-V-I / vi-IV-I-V / 12-bar Blues 等)
- 每种带情绪权重(emotion_tags: 8 档情绪的 0-1 匹配度)
- suggest_progressions(key, emotion, n=5~8) 返回排序后的 n 候选
- 大调返回大调候选;小调返回小调候选(转调后输出 Roman Numeral)

候选数限制:
- Phase 1 v0(本期): 5-8 候选(任务契约)
- Phase 1 v1(9/16 ~ 9/20): 30+ 经典进行 + 自定义输入
"""
from __future__ import annotations
from typing import List, Dict, Optional

# 8 档情绪(与 emotion_keyword.py 同步)
EMOTIONS = ["happy", "sad", "tense", "calm", "epic", "tender", "mysterious", "jazzy"]

# 12 种经典进行模板
# format: name, roman_numerals_major (大调 4 小节), roman_numerals_minor (小调 4 小节),
#         description, emotion_tags (dict[emotion] = 0~1)
PROGRESSIONS_LIBRARY: List[Dict] = [
    {
        "id": "I-V-vi-IV",
        "name": "Pop Anthem",
        "roman_major": ["I", "V", "vi", "IV"],
        "roman_minor": ["i", "V", "VI", "iv"],
        "description": "流行金曲标配,4 和弦循环,记忆点强,适合副歌",
        "emotion_tags": {"happy": 0.9, "sad": 0.3, "tense": 0.2, "calm": 0.4, "epic": 0.5, "tender": 0.5, "mysterious": 0.2, "jazzy": 0.1},
    },
    {
        "id": "vi-IV-I-V",
        "name": "Emotional Ballad",
        "roman_major": ["vi", "IV", "I", "V"],
        "roman_minor": ["i", "iv", "VII", "V"],  # 小调视角常用
        "description": "情感抒发型,常用于副歌前的递进,适合抒情曲",
        "emotion_tags": {"happy": 0.4, "sad": 0.9, "tense": 0.3, "calm": 0.5, "epic": 0.5, "tender": 0.9, "mysterious": 0.4, "jazzy": 0.2},
    },
    {
        "id": "ii-V-I",
        "name": "Jazz Turnaround",
        "roman_major": ["ii", "V", "I", "I"],
        "roman_minor": ["ii°", "V", "i", "i"],
        "description": "爵士万能进行,最强功能性终止,可加 9/11/13 扩展",
        "emotion_tags": {"happy": 0.4, "sad": 0.4, "tense": 0.5, "calm": 0.6, "epic": 0.4, "tender": 0.5, "mysterious": 0.5, "jazzy": 1.0},
    },
    {
        "id": "I-vi-IV-V",
        "name": "50s Doo-wop",
        "roman_major": ["I", "vi", "IV", "V"],
        "roman_minor": ["i", "VI", "iv", "V"],
        "description": "50 年代摇滚经典,简洁明快,Earth Angel 风",
        "emotion_tags": {"happy": 0.8, "sad": 0.3, "tense": 0.1, "calm": 0.7, "epic": 0.2, "tender": 0.6, "mysterious": 0.1, "jazzy": 0.3},
    },
    {
        "id": "I-IV-V-I",
        "name": "Folk Classic",
        "roman_major": ["I", "IV", "V", "I"],
        "roman_minor": ["i", "iv", "V", "i"],
        "description": "民谣经典终止,和声稳定,适合叙事",
        "emotion_tags": {"happy": 0.5, "sad": 0.4, "tense": 0.2, "calm": 0.9, "epic": 0.3, "tender": 0.7, "mysterious": 0.2, "jazzy": 0.2},
    },
    {
        "id": "I-bVII-IV-I",
        "name": "Mixolydian Vibe",
        "roman_major": ["I", "bVII", "IV", "I"],
        "roman_minor": ["i", "bVII", "iv", "i"],
        "description": "Mixolydian 调式风味,摇滚/凯尔特常用,带悬疑色彩",
        "emotion_tags": {"happy": 0.4, "sad": 0.3, "tense": 0.5, "calm": 0.4, "epic": 0.8, "tender": 0.3, "mysterious": 0.5, "jazzy": 0.3},
    },
    {
        "id": "vi-IV-I-V-",
        "name": "Andalusian Cadence",
        "roman_major": ["vi", "IV", "I", "V"],  # 用 I-V 强收
        "roman_minor": ["i", "VII", "VI", "V"],
        "description": "安达卢西亚终止,西班牙/弗拉门戈风,常见于 Stardust 风",
        "emotion_tags": {"happy": 0.3, "sad": 0.7, "tense": 0.5, "calm": 0.4, "epic": 0.5, "tender": 0.4, "mysterious": 0.7, "jazzy": 0.3},
    },
    {
        "id": "i-iv-V-i",
        "name": "Natural Minor",
        "roman_major": ["i", "iv", "V", "i"],  # 小调被用于大调场景下作 borrow
        "roman_minor": ["i", "iv", "V", "i"],
        "description": "自然小调标准进行,忧郁深沉,适合叙事",
        "emotion_tags": {"happy": 0.1, "sad": 1.0, "tense": 0.3, "calm": 0.5, "epic": 0.4, "tender": 0.7, "mysterious": 0.5, "jazzy": 0.2},
    },
    {
        "id": "i-VI-III-VII",
        "name": "Epic Progression",
        "roman_major": ["i", "bVI", "bIII", "bVII"],  # 同名小调化
        "roman_minor": ["i", "bVI", "bIII", "bVII"],
        "description": "史诗进行,影视/Hans Zimmer 风,大调下沉 4 级即得同名小调",
        "emotion_tags": {"happy": 0.2, "sad": 0.6, "tense": 0.7, "calm": 0.2, "epic": 1.0, "tender": 0.3, "mysterious": 0.6, "jazzy": 0.1},
    },
    {
        "id": "12-bar-blues",
        "name": "12-bar Blues",
        "roman_major": ["I", "I", "I", "I", "IV", "IV", "I", "I", "V", "IV", "I", "V"],
        "roman_minor": ["i", "i", "i", "i", "iv", "iv", "i", "i", "V", "iv", "i", "V"],
        "description": "12 小节蓝调,蓝调/摇滚根基,5 级属七常用",
        "emotion_tags": {"happy": 0.5, "sad": 0.6, "tense": 0.4, "calm": 0.3, "epic": 0.4, "tender": 0.3, "mysterious": 0.4, "jazzy": 0.7},
    },
    {
        "id": "I-bIII-IV-bVI",
        "name": "Doo-wop Descend",
        "roman_major": ["I", "bIII", "IV", "bVI"],
        "roman_minor": ["i", "bIII", "iv", "bVI"],
        "description": "下行四度循环,带复古忧伤,50 年代慢板风",
        "emotion_tags": {"happy": 0.2, "sad": 0.8, "tense": 0.4, "calm": 0.5, "epic": 0.3, "tender": 0.8, "mysterious": 0.6, "jazzy": 0.3},
    },
    {
        "id": "I-V-vi-iii-IV",
        "name": "Descending Circle",
        "roman_major": ["I", "V", "vi", "iii", "IV", "I", "IV", "V"],
        "roman_minor": ["i", "V", "VI", "iv", "i", "V", "iv", "V"],
        "description": "下行五度长链,Pachelbel Canon 变体,适合 8 小节结构",
        "emotion_tags": {"happy": 0.4, "sad": 0.6, "tense": 0.3, "calm": 0.8, "epic": 0.7, "tender": 0.7, "mysterious": 0.4, "jazzy": 0.3},
    },
]


def suggest_progressions(
    key: str,
    emotion: str,
    n: int = 6,
) -> List[Dict]:
    """根据调性和情绪返回 5-8 候选和弦进行

    Args:
        key: 调性,如 "C", "Am", "G", "Em"(大小写自动归一)
        emotion: 8 档之一: happy/sad/tense/calm/epic/tender/mysterious/jazzy
        n: 候选数,默认 6,范围 [5, 8]

    Returns:
        List[Dict]: 排序后的候选列表,每项含 id / name / roman / description / emotion_score

    Examples:
        >>> result = suggest_progressions("C", "happy", n=5)
        >>> len(result) == 5
        True
        >>> result[0]["id"]  # 应该是 happy 权重最高的
        'I-V-vi-IV'
    """
    if emotion not in EMOTIONS:
        raise ValueError(f"emotion must be one of {EMOTIONS}, got {emotion!r}")
    if not (5 <= n <= 8):
        raise ValueError(f"n must be in [5, 8], got {n}")

    # 判断大小调(支持 "Am", "a", "a minor" 等变体)
    is_minor = key.strip().lower().endswith("m") or "minor" in key.lower()
    key_canonical = key.strip()
    # 去掉 "m" 后缀或 "minor" 后缀做规范化(让 KeyNormalizer 处理)
    if is_minor:
        # "Am" -> "A", "A minor" -> "A"
        base = key_canonical.rstrip("m").rstrip("M").strip()
        if base.lower().endswith("inor"):
            base = base[:-5].strip()
        key_canonical = base + "m"

    # 计算每个进行的情绪得分
    scored = []
    for prog in PROGRESSIONS_LIBRARY:
        score = prog["emotion_tags"].get(emotion, 0.0)
        roman = prog["roman_minor"] if is_minor else prog["roman_major"]
        scored.append({
            "id": prog["id"],
            "name": prog["name"],
            "roman": roman,
            "description": prog["description"],
            "emotion_score": round(score, 2),
            "key": key_canonical,
            "is_minor": is_minor,
        })

    # 按分数降序,前 n 个
    scored.sort(key=lambda x: x["emotion_score"], reverse=True)
    return scored[:n]


if __name__ == "__main__":
    # 烟囱测试
    for emo in EMOTIONS:
        result = suggest_progressions("C", emo, n=5)
        top = result[0]
        print(f"{emo:12s} -> {top['id']:18s} ({top['name']:20s}) score={top['emotion_score']}")
    print()
    print("C minor / sad:", [r["id"] for r in suggest_progressions("Am", "sad", n=5)])