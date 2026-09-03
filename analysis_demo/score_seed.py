"""
score_seed.py · MusicAdvisor Phase 0 任务 7a 种子乐谱加载器

==========================================================================
项目:    MusicAdvisor
模块:    Phase 0 / 任务 7a 起步(10 首种子 + 自动化脚本骨架)
作者:    19-音乐-Music 顾问(T5 03:00 启动 Phase 0 任务 7)
日期:    2026-09-04
状态:    Phase 0 占位 — 10 首种子加载 + 契约校验,真实音频分析待 Phase 1
关联:    项目开发计划.md §5 任务 7a
         analysis_demo/scores/seed_10.json
         InspirationIndex.md(下次巡检登记)
         .Log/巡检-音乐-20260904.md P0 建议
==========================================================================

设计意图
--------
1. Phase 0 不强求真实音频分析,先把"种子数据 + 加载 + 契约校验"骨架立住
2. seed_10.json 是任务 7 总目标 50 首的 1/5,本脚本契约固定后,任务 7b(续做 40 首)只换数据源不换代码
3. 输出结构化 summary,供 Phase 1 乐理问答 demo 检索 / 风格拆解匹配 / InspirationIndex 补登记

运行方式
--------
    # 无依赖模式(Python 3.7+ 标准库):
    python3 analysis_demo/score_seed.py

    # 输出 JSON 到文件供下游使用:
    python3 analysis_demo/score_seed.py --output analysis_demo/scores/seed_10_summary.json
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List


# ---------------------------------------------------------------------------
# 1. 路径与契约定义
# ---------------------------------------------------------------------------
SEED_PATH = Path(__file__).parent / "scores" / "seed_10.json"

REQUIRED_SONG_FIELDS = [
    "id", "title", "artist", "year", "style",
    "key", "scale", "time_signature", "bpm",
    "duration_sec", "form", "chord_progression",
    "chord_count_est", "tags",
]


# ---------------------------------------------------------------------------
# 2. 加载与校验
# ---------------------------------------------------------------------------
def load_seed(path: Path = SEED_PATH) -> Dict[str, Any]:
    """加载 seed JSON,失败时抛清晰错误(避免 Phase 1 静默吞错)。"""
    if not path.exists():
        raise FileNotFoundError(
            f"种子乐谱文件不存在: {path}。"
            f"任务 7a 产物,请确认 .plan/20260904.md 已 commit seed_10.json。"
        )
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    _validate(data)
    return data


def _validate(data: Dict[str, Any]) -> None:
    """契约校验:meta + 必备字段 + 数量。Phase 1 沿用同一校验,只扩字段白名单。"""
    if "_meta" not in data or "songs" not in data:
        raise ValueError("seed JSON 缺少 _meta 或 songs 顶层字段")
    songs: List[Dict[str, Any]] = data["songs"]
    for i, song in enumerate(songs):
        missing = [f for f in REQUIRED_SONG_FIELDS if f not in song]
        if missing:
            raise ValueError(
                f"songs[{i}]({song.get('id', '?')}) 缺字段: {missing}"
            )
        if not isinstance(song["chord_progression"], list) or len(song["chord_progression"]) == 0:
            raise ValueError(
                f"songs[{i}]({song['id']}) chord_progression 必须为非空 list"
            )
    # ID 唯一性
    ids = [s["id"] for s in songs]
    if len(ids) != len(set(ids)):
        dup = [k for k, v in Counter(ids).items() if v > 1]
        raise ValueError(f"重复的 song id: {dup}")


# ---------------------------------------------------------------------------
# 3. 汇总报告
# ---------------------------------------------------------------------------
def summarize(data: Dict[str, Any]) -> Dict[str, Any]:
    """生成 4 维汇总,供 README / 下游 Agent 检索。"""
    songs = data["songs"]
    style_counter: Counter = Counter()
    key_counter: Counter = Counter()
    bpms: List[int] = []
    years: List[int] = []
    for s in songs:
        # style 形如 "流行 · 摇滚民谣",按 · 拆分取主类
        main_style = s["style"].split("·")[0].strip()
        style_counter[main_style] += 1
        # key 形如 "C major" / "A minor",按大小调分组
        mode = "大调" if "major" in s["key"].lower() else "小调"
        key_counter[mode] += 1
        bpms.append(s["bpm"])
        years.append(s["year"])
    return {
        "meta": data["_meta"],
        "total_songs": len(songs),
        "by_style": dict(style_counter),
        "by_key_mode": dict(key_counter),
        "bpm_range": [min(bpms), max(bpms)] if bpms else [0, 0],
        "year_range": [min(years), max(years)] if years else [0, 0],
        "song_ids": [s["id"] for s in songs],
        "phase_0_target": 50,
        "phase_0_progress": f"{len(songs)}/50",
        "task_7b_pending": 40,
    }


# ---------------------------------------------------------------------------
# 4. 入口
# ---------------------------------------------------------------------------
def main() -> int:
    out_arg = sys.argv[1] if len(sys.argv) > 1 else None
    # 支持 --output 简写:python3 score_seed.py --output path.json
    output_path: Path | None = None
    if out_arg == "--output" and len(sys.argv) > 2:
        output_path = Path(sys.argv[2])
    try:
        data = load_seed()
    except (FileNotFoundError, ValueError) as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 1
    summary = summarize(data)
    summary_text = json.dumps(summary, ensure_ascii=False, indent=2)
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(summary_text + "\n", encoding="utf-8")
        print(f"[OK] summary 已写入 {output_path}({len(summary_text)} 字节)")
    else:
        print(summary_text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
