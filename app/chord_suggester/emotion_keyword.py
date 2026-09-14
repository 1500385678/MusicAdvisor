"""情绪关键词 → 和弦偏好映射

8 档情绪(与 chord_progressions.py 同步):
- happy / sad / tense / calm / epic / tender / mysterious / jazzy

每个情绪档位:
- 中文关键词集(用户输入"快乐"→ happy)
- 英文关键词集(用户输入"happy"/"uplifting"→ happy)
- 和弦偏好摘要(给 LLM prompt 工程参考)
- 推荐 BPM 范围(给试听节奏建议)
"""
from __future__ import annotations
from typing import Dict, List, Optional

EMOTION_KEYWORDS: Dict[str, Dict] = {
    "happy": {
        "zh": ["快乐", "欢快", "开心", "高兴", "明亮", "阳光", "活泼", "喜庆", "happy", "joy"],
        "en": ["happy", "joyful", "cheerful", "bright", "sunny", "uplifting", "playful"],
        "chord_preference": "大调 I / IV / V 三主和弦为主,可加 vi 短暂小调化",
        "bpm_range": (100, 140),
        "color_words": ["开心", "欢快"],
    },
    "sad": {
        "zh": ["忧伤", "悲伤", "忧郁", "哀愁", "伤感", "悲凉", "凄美", "深沉"],
        "en": ["sad", "melancholy", "sorrow", "gloomy", "blue", "somber", "heartbroken"],
        "chord_preference": "小调 i / iv / V 为骨,可加 bVI / bVII 下行",
        "bpm_range": (60, 90),
        "color_words": ["忧伤", "忧郁"],
    },
    "tense": {
        "zh": ["紧张", "悬疑", "紧迫", "压迫", "焦虑", "不安", "张力", "悬疑"],
        "en": ["tense", "anxious", "uneasy", "suspenseful", "pressured", "restless"],
        "chord_preference": "增三/减七 + 半音进行 + ii°-V 链,功能性强",
        "bpm_range": (110, 150),
        "color_words": ["紧张", "悬疑"],
    },
    "calm": {
        "zh": ["平静", "安宁", "宁静", "放松", "冥想", "禅意", "舒缓", "禅"],
        "en": ["calm", "peaceful", "serene", "tranquil", "relaxed", "meditative"],
        "chord_preference": "I-IV-V 慢节奏 + 6/9 延音和弦 + Sus 挂留",
        "bpm_range": (60, 80),
        "color_words": ["平静", "宁静"],
    },
    "epic": {
        "zh": ["史诗", "壮阔", "宏伟", "震撼", "英雄", "大气", "恢弘", "电影感"],
        "en": ["epic", "grand", "heroic", "cinematic", "majestic", "powerful"],
        "chord_preference": "同名小调化大调(i / bVI / bIII / bVII) + 强属挂留 + 转调",
        "bpm_range": (90, 120),
        "color_words": ["史诗", "壮阔"],
    },
    "tender": {
        "zh": ["温柔", "柔情", "细腻", "缠绵", "温馨", "暖心", "蜜意", "甜美"],
        "en": ["tender", "gentle", "sweet", "warm", "intimate", "loving", "soft"],
        "chord_preference": "vi-IV-I-V 或 I-vi-IV-V,加 9/11 扩展音,女性化色彩",
        "bpm_range": (70, 100),
        "color_words": ["温柔", "柔情"],
    },
    "mysterious": {
        "zh": ["神秘", "玄妙", "魔幻", "异域", "迷离", "梦境", "空灵", "诡谲"],
        "en": ["mysterious", "enigmatic", "ethereal", "dreamy", "exotic", "otherworldly"],
        "chord_preference": "调式互换(Mixolydian / Dorian / Lydian)+ 减七和弦 + 全音阶",
        "bpm_range": (80, 110),
        "color_words": ["神秘", "空灵"],
    },
    "jazzy": {
        "zh": ["爵士", "摇摆", "波萨", "拉丁", "复古", "酒吧风", "慵懒"],
        "en": ["jazzy", "swing", "bossa", "latin", "vintage", "sophisticated", "sultry"],
        "chord_preference": "ii-V-I 9/11/13 + 蓝调音 + 调式互换,扩展和弦密度高",
        "bpm_range": (90, 130),
        "color_words": ["爵士", "摇摆"],
    },
}


class EmotionMapper:
    """情绪关键词 → 标准情绪档位的映射器

    用法:
        mapper = EmotionMapper()
        emotion, confidence = mapper.match("快乐的早晨")  # ("happy", 1.0)
        emotion, confidence = mapper.match("忧郁的夜")    # ("sad", 1.0)
        emotion, confidence = mapper.match("epic movie")   # ("epic", 1.0)
    """

    def __init__(self) -> None:
        self._build_index()

    def _build_index(self) -> None:
        # 反向索引: 关键词 → 标准情绪
        self._keyword_index: Dict[str, str] = {}
        for emotion, payload in EMOTION_KEYWORDS.items():
            for kw in payload["zh"] + payload["en"]:
                # 大小写不敏感
                self._keyword_index[kw.lower()] = emotion

    def match(self, text: str) -> tuple[Optional[str], float]:
        """从自由文本匹配情绪档位

        策略: 任意关键词命中即返回,confidence=1.0;多情绪同时命中取第一个;
              0 命中返回 (None, 0.0)

        Args:
            text: 自由文本,中英文均可

        Returns:
            (emotion, confidence): emotion 为 8 档之一,或 None
        """
        text_lower = text.lower()
        for keyword, emotion in self._keyword_index.items():
            if keyword in text_lower:
                return emotion, 1.0
        return None, 0.0

    def list_keywords(self, emotion: str) -> List[str]:
        """列出某情绪的所有关键词(中英文)"""
        if emotion not in EMOTION_KEYWORDS:
            raise ValueError(f"emotion must be one of {list(EMOTION_KEYWORDS)}, got {emotion!r}")
        return EMOTION_KEYWORDS[emotion]["zh"] + EMOTION_KEYWORDS[emotion]["en"]

    def get_bpm_range(self, emotion: str) -> tuple[int, int]:
        """返回某情绪的建议 BPM 范围(给试听节奏建议)"""
        if emotion not in EMOTION_KEYWORDS:
            raise ValueError(f"emotion must be one of {list(EMOTION_KEYWORDS)}, got {emotion!r}")
        return EMOTION_KEYWORDS[emotion]["bpm_range"]


if __name__ == "__main__":
    mapper = EmotionMapper()
    test_texts = ["快乐的早晨", "sad and blue", "史诗级电影配乐", "爵士酒吧风", "calm meditation", "悬疑大片", "温柔情歌", "神秘空灵"]
    for txt in test_texts:
        emo, conf = mapper.match(txt)
        print(f"{txt:20s} -> {emo} (conf={conf})")