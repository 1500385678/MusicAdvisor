"""MIDI 元数据加载与索引读取。

v0 骨架:Phase 1 续做替换为 mido/pretty_midi 真链路读 .mid 二进制;
本骨架仅 metadata 索引层读取,从 index_meta.json + midi_tags_v0.json schema
构造 MidiMetadata dataclass。

关键点:
    - 不直接绑死 .mid 二进制文件(版权风险,见 项目开发计划.md §8)
    - 元数据来源:本包 index_meta.json + schema 字典(midi_tags_v0.json)
    - Phase 1 真实模式激活时,新增 mido.load() 链路读取真实 .mid,元数据优先取 .mid header,缺时回退 index_meta.json
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class MidiMetadata:
    """MIDI 元数据(dataclass / JSON 可序列化)。

    Attributes:
        id: 全局唯一 ID(如 M-001)。
        title: 标题。
        style_primary: 一级风格(ST-XX + 中文名,如 "ST-01 流行")。
        style_subtag: 二级子标签(如 "抒情流行")。
        mood: 情绪列表(MO-XX + 中文名)。
        tempo: BPM 档位(TP-XX + 中文名)。
        bpm: 实际 BPM 数值。
        key: 调性(KY-XX + 中英文,如 "KY-14 d minor")。
        scale: 音阶描述(如 "自然小调 + Dorian 借")。
        time_signature: 拍号(如 "4/4")。
        duration_sec: 时长(秒)。
        tags: 自由文本标签列表。
        note_count: 音符数(真实 MIDI 时填,本骨架可选)。
    """

    id: str
    title: str
    style_primary: str
    style_subtag: str
    mood: List[str]
    tempo: str
    bpm: int
    key: str
    scale: str
    time_signature: str
    duration_sec: int
    tags: List[str]
    note_count: int = 0

    def to_dict(self) -> Dict:
        return asdict(self)


class MidiLoader:
    """MIDI 元数据加载器(v0 骨架:从 index_meta.json 读)。"""

    INDEX_FILE = "index_meta.json"

    def __init__(self, index_path: Optional[Path] = None) -> None:
        """初始化加载器。

        Args:
            index_path: index_meta.json 的绝对路径;None 时自动定位本包目录。
        """
        self.index_path = index_path or self._default_index_path()
        self._cache: Optional[List[MidiMetadata]] = None

    @staticmethod
    def _default_index_path() -> Path:
        """默认 index_meta.json 路径:本包目录下。"""
        return Path(__file__).resolve().parent / "index_meta.json"

    def load(self) -> List[MidiMetadata]:
        """加载 index_meta.json 全部条目录入 MidiMetadata 列表(惰性 + 缓存)。

        Returns:
            元数据列表。
        """
        if self._cache is not None:
            return self._cache

        if not self.index_path.exists():
            self._cache = []
            return self._cache

        with self.index_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        items = data.get("entries", data if isinstance(data, list) else [])
        out: List[MidiMetadata] = []
        for item in items:
            out.append(
                MidiMetadata(
                    id=item["id"],
                    title=item.get("title", ""),
                    style_primary=item.get("style_primary", ""),
                    style_subtag=item.get("style_subtag", ""),
                    mood=item.get("mood", []),
                    tempo=item.get("tempo", ""),
                    bpm=item.get("bpm", 0),
                    key=item.get("key", ""),
                    scale=item.get("scale", ""),
                    time_signature=item.get("time_signature", ""),
                    duration_sec=item.get("duration_sec", 0),
                    tags=item.get("tags", []),
                    note_count=item.get("note_count", 0),
                )
            )
        self._cache = out
        return out

    def get_by_id(self, midi_id: str) -> Optional[MidiMetadata]:
        """按 ID 查询单条 MIDI 元数据。"""
        for m in self.load():
            if m.id == midi_id:
                return m
        return None

    def count(self) -> int:
        """返回索引条目总数。"""
        return len(self.load())


def load_metadata(index_path: Optional[Path] = None) -> List[MidiMetadata]:
    """便捷函数:加载全部 MIDI 元数据。

    Args:
        index_path: index_meta.json 路径;None 时默认。
    """
    return MidiLoader(index_path=index_path).load()
