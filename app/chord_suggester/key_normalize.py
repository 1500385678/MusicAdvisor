"""调性归一化:24 调(12 大 + 12 小)→ 内部表示 + Roman Numeral 拼写

支持输入变体:
- "C", "C major", "C大调", "C大"
- "Am", "A minor", "A小调", "A小"
- 等音: "Db" ↔ "C#", "Eb" ↔ "D#", 等

输出规范:
- canonical_key: "C", "Am", "F#m" 等标准名
- is_minor: bool
- pitch_class: 0-11(C=0, C#/Db=1, ..., B=11)
- relative_minor/major: 大调 ↔ 小调(Am 是 C 的关系小调)
"""
from __future__ import annotations
from typing import Optional, Tuple

# 12 个音名(用 # 记法为标准)
SHARP_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
FLAT_NAMES = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]

# 12 大调 + 12 小调 共 24 调
SUPPORTED_KEYS = (
    # 12 大调
    [f"{n}" for n in SHARP_NAMES] +
    # 12 小调(加 m 后缀)
    [f"{n}m" for n in SHARP_NAMES]
)

# 等音映射(flat → sharp)
ENHARMONIC_MAP = {
    "Db": "C#", "Eb": "D#", "Gb": "F#", "Ab": "G#", "Bb": "A#",
    "db": "C#", "eb": "D#", "gb": "F#", "ab": "G#", "bb": "A#",
}


class KeyNormalizer:
    """调性字符串归一化器

    用法:
        n = KeyNormalizer()
        canonical = n.normalize("c")            # "C"
        canonical = n.normalize("Am")           # "Am"
        canonical = n.normalize("A minor")      # "Am"
        canonical = n.normalize("Db major")     # "C#"
        canonical = n.normalize("Bb 小调")       # "A#"
    """

    # 中文后缀 → 大小调
    ZH_SUFFIX_MAJOR = ("大调", "大")
    ZH_SUFFIX_MINOR = ("小调", "小")

    # 英文后缀 → 大小调
    EN_SUFFIX_MAJOR = ("major", "maj", "M")
    EN_SUFFIX_MINOR = ("minor", "min", "m")

    def normalize(self, raw: str) -> str:
        """归一化调性字符串

        Args:
            raw: 调性原始输入,如 "C", "Am", "C major", "A小调", "Db"

        Returns:
            标准调性名,大调如 "C"/"F#",小调如 "Am"/"C#m"

        Raises:
            ValueError: 调性无法识别
        """
        if not raw or not isinstance(raw, str):
            raise ValueError(f"key must be non-empty string, got {raw!r}")

        s = raw.strip()
        if not s:
            raise ValueError(f"key must be non-empty, got {raw!r}")

        # 1. 检测大小调
        is_minor = self._detect_minor(s)
        # 2. 去掉后缀(英文 + 中文)
        s_clean = self._strip_suffix(s)
        # 3. 提取基础音名(字母 + 可选 #/b)
        base = self._extract_pitch(s_clean)
        # 4. 等音归一(flat → sharp)
        if base in ENHARMONIC_MAP:
            base = ENHARMONIC_MAP[base]
        # 5. 验证基础音名合法
        if base not in SHARP_NAMES:
            raise ValueError(f"unrecognized pitch {base!r} from input {raw!r}")
        # 6. 拼标准名
        return base + ("m" if is_minor else "")

    def parse(self, canonical: str) -> dict:
        """解析标准调性名为结构化字典

        Returns:
            {"canonical": "C"/"Am", "is_minor": bool, "pitch_class": 0-11, "root": "C"/"A"}
        """
        if canonical not in SUPPORTED_KEYS:
            raise ValueError(f"canonical key must be one of 24, got {canonical!r}")
        is_minor = canonical.endswith("m")
        root = canonical[:-1] if is_minor else canonical
        pc = SHARP_NAMES.index(root)
        return {
            "canonical": canonical,
            "is_minor": is_minor,
            "pitch_class": pc,
            "root": root,
        }

    def relative_key(self, canonical: str) -> str:
        """关系调转换:大调 ↔ 小调(C ↔ Am)

        Returns:
            关系调名(若是大调返回关系小调,反之亦然)
        """
        info = self.parse(canonical)
        if info["is_minor"]:
            # 小调 → 关系大调:根音 + 3 半音
            rel_pc = (info["pitch_class"] + 3) % 12
            return SHARP_NAMES[rel_pc]
        else:
            # 大调 → 关系小调:根音 - 3 半音
            rel_pc = (info["pitch_class"] - 3) % 12
            return SHARP_NAMES[rel_pc] + "m"

    def _detect_minor(self, s: str) -> bool:
        """检测字符串是否表示小调"""
        s_lower = s.lower()
        # 英文后缀
        for suf in self.EN_SUFFIX_MINOR:
            if s_lower.endswith(suf):
                return True
        # 中文后缀
        for suf in self.ZH_SUFFIX_MINOR:
            if s.endswith(suf):
                return True
        # 大写 M 通常表示大调,小写 m 表示小调,但 Am 这种 "Am" 是 "A" + "m"
        if s.endswith("m") and not s.endswith("M"):
            return True
        return False

    def _strip_suffix(self, s: str) -> str:
        """去掉大小调后缀"""
        for suf in self.EN_SUFFIX_MAJOR + self.EN_SUFFIX_MINOR:
            if s.lower().endswith(suf):
                return s[:-len(suf)]
        for suf in self.ZH_SUFFIX_MAJOR + self.ZH_SUFFIX_MINOR:
            if s.endswith(suf):
                return s[:-len(suf)]
        return s

    def _extract_pitch(self, s: str) -> str:
        """从去后缀字符串提取基础音名(字母 + 可选 #/b,大小写不敏感)"""
        if not s:
            raise ValueError("empty pitch after stripping suffix")
        s_clean = s.strip()
        # 首字母(大写化) + 可能的 # 或 b
        pitch = s_clean[0].upper()
        if len(s_clean) > 1 and s_clean[1] in ("#", "b"):
            pitch += s_clean[1]
        return pitch


if __name__ == "__main__":
    n = KeyNormalizer()
    test_inputs = ["C", "Am", "A minor", "A小调", "Db major", "Bb 大调", "F#", "f# minor", "g#m", ""]
    for inp in test_inputs:
        try:
            canon = n.normalize(inp)
            info = n.parse(canon)
            rel = n.relative_key(canon)
            print(f"{inp!r:20s} -> {canon:5s} | pc={info['pitch_class']:2d} | minor={info['is_minor']} | rel={rel}")
        except ValueError as e:
            print(f"{inp!r:20s} -> ERROR: {e}")