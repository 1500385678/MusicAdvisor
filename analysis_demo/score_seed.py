"""
score_seed.py · MusicAdvisor Phase 0 任务 7 种子乐谱加载器(批次合并版)

==========================================================================
项目:    MusicAdvisor
模块:    Phase 0 / 任务 7(7a 10 + 7b 第 2 批 20 + 7b 第 3 批 20 = 50/50 = 100% 满)
作者:    19-音乐-Music 顾问(T5 03:00 启动 Phase 0 任务 7 · T1 03:00 续做第 3 批前 10
                  T5 03:00 续做第 3 批后 10,T4 14 工作日 0 输出 T5 自救闭环第 3 批 20/20)
日期:    2026-09-04 起步 · 2026-09-06 扩到 batch 模式(7a 10 + 7b 第 2 批 20)
                  2026-09-08 续做 7b 第 3 批前 10(40/50 = 80% 完成)
                  2026-09-09 续做 7b 第 3 批后 10(50/50 = 100% 满 · 第 3 批 20/20 闭环)
状态:    Phase 0 占位 — 50 首种子加载 + 契约校验,真实音频分析待 Phase 1
关联:    项目开发计划.md §5 任务 7a / 7b
         analysis_demo/scores/seed_10.json(7a 10 首)
         analysis_demo/scores/seed_20_b.json(7b 第 2 批 20 首,2026-09-06 新增)
         analysis_demo/scores/seed_20_c.json(7b 第 3 批前 10 首,2026-09-08 T1 新增)
         analysis_demo/scores/seed_10_d.json(7b 第 3 批后 10 首,2026-09-09 T5 新增,本份)
         InspirationIndex.md(下次巡检登记)
         .Log/巡检-音乐-20260904.md P0 建议 · .Log/巡检-音乐-20260906.md P0 任务 7b 0 续做
         .Log/巡检-音乐-20260909.md P0 #1 任务 7b 第 3 批后 10 首启动 · .plan/20260909.md 自救
==========================================================================

设计意图
--------
1. Phase 0 不强求真实音频分析,先把"种子数据 + 加载 + 契约校验"骨架立住
2. seed_10.json 是任务 7 总目标 50 首的 1/5(7a),seed_20_b.json 是第 2 批(7b);
   seed_20_c.json + seed_10_d.json 是 7b 第 3 批 20 首拆 10+10,4 批同契约
3. 加载器支持 --batch all 自动合并多批次,契约固定,7b 第 4 批续做只换数据源不换代码
4. 输出结构化 summary,供 Phase 1 乐理问答 demo 检索 / 风格拆解匹配 / InspirationIndex 补登记

运行方式
--------
    # 无依赖模式(Python 3.7+ 标准库):
    python3 analysis_demo/score_seed.py                          # 单批 seed_10
    python3 analysis_demo/score_seed.py --batch all              # 合并 4 批 50 首
    python3 analysis_demo/score_seed.py --batch seed_20_b         # 单批 seed_20_b
    python3 analysis_demo/score_seed.py --batch seed_20_c         # 单批 seed_20_c
    python3 analysis_demo/score_seed.py --batch seed_10_d         # 单批 seed_10_d(本份 9/9 新增)

    # 输出 JSON 到文件供下游使用:
    python3 analysis_demo/score_seed.py --batch all --output analysis_demo/scores/seed_50_summary.json
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
SCORES_DIR = Path(__file__).parent / "scores"

# 批次注册表 — 新增批次时只需往 BATCHES 追加一项,无需改加载/校验逻辑
BATCHES: Dict[str, Path] = {
    "seed_10":   SCORES_DIR / "seed_10.json",     # 任务 7a · 流行 4 + 爵士 3 + 古典 3
    "seed_20_b": SCORES_DIR / "seed_20_b.json",   # 任务 7b 第 2 批 · 摇滚 5 + 民谣 5 + 电子 5 + 世界音乐 5
    "seed_20_c": SCORES_DIR / "seed_20_c.json",   # 任务 7b 第 3 批前 10 首 · 流行新 4 + 爵士新 3 + 电子新 3(2026-09-08 T1)
    "seed_10_d": SCORES_DIR / "seed_10_d.json",   # 任务 7b 第 3 批后 10 首 · 古典 3 + 巴洛克 2 + 民族 3 + 民歌 2(2026-09-09 T5)
}

REQUIRED_SONG_FIELDS = [
    "id", "title", "artist", "year", "style",
    "key", "scale", "time_signature", "bpm",
    "duration_sec", "form", "chord_progression",
    "chord_count_est", "tags",
]

PHASE_0_TARGET = 50  # 任务 7 总目标(7a 10 + 7b 40)


# ---------------------------------------------------------------------------
# 2. 加载与校验
# ---------------------------------------------------------------------------
def load_batch(name: str) -> Dict[str, Any]:
    """加载单个批次 JSON,失败时抛清晰错误(避免 Phase 1 静默吞错)。"""
    if name not in BATCHES:
        raise ValueError(f"未知批次: {name},当前注册: {list(BATCHES.keys())}")
    path = BATCHES[name]
    if not path.exists():
        raise FileNotFoundError(
            f"批次 {name} 文件不存在: {path}。"
            f"任务 7 产物,请确认 {name}.json 已 commit。"
        )
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    _validate(data, batch_name=name)
    return data


def load_all(batches: List[str]) -> Dict[str, Any]:
    """合并多个批次为单数据集(meta 取首批,_meta.merged_from 标注来源)。"""
    if not batches:
        raise ValueError("至少需要 1 个批次")
    merged_songs: List[Dict[str, Any]] = []
    first_meta: Dict[str, Any] = {}
    sources: List[str] = []
    for b in batches:
        data = load_batch(b)
        if not first_meta:
            first_meta = data["_meta"]
        merged_songs.extend(data["songs"])
        sources.append(b)
    first_meta["merged_from"] = sources
    first_meta["merged_total_songs"] = len(merged_songs)
    return {"_meta": first_meta, "songs": merged_songs}


def _validate(data: Dict[str, Any], batch_name: str = "?") -> None:
    """契约校验:meta + 必备字段 + 数量 + ID 唯一性。Phase 1 沿用同一校验,只扩字段白名单。"""
    if "_meta" not in data or "songs" not in data:
        raise ValueError(f"[{batch_name}] seed JSON 缺少 _meta 或 songs 顶层字段")
    songs: List[Dict[str, Any]] = data["songs"]
    for i, song in enumerate(songs):
        missing = [f for f in REQUIRED_SONG_FIELDS if f not in song]
        if missing:
            raise ValueError(
                f"[{batch_name}] songs[{i}]({song.get('id', '?')}) 缺字段: {missing}"
            )
        if not isinstance(song["chord_progression"], list) or len(song["chord_progression"]) == 0:
            raise ValueError(
                f"[{batch_name}] songs[{i}]({song['id']}) chord_progression 必须为非空 list"
            )
    # ID 唯一性(单批内)
    ids = [s["id"] for s in songs]
    if len(ids) != len(set(ids)):
        dup = [k for k, v in Counter(ids).items() if v > 1]
        raise ValueError(f"[{batch_name}] 重复的 song id: {dup}")


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
    meta = data["_meta"]
    return {
        "meta": meta,
        "total_songs": len(songs),
        "by_style": dict(style_counter),
        "by_key_mode": dict(key_counter),
        "bpm_range": [min(bpms), max(bpms)] if bpms else [0, 0],
        "year_range": [min(years), max(years)] if years else [0, 0],
        "song_ids": [s["id"] for s in songs],
        "merged_from": meta.get("merged_from", [meta.get("batch", "single")]),
        "phase_0_target": PHASE_0_TARGET,
        "phase_0_progress": f"{len(songs)}/{PHASE_0_TARGET}",
        "task_7b_pending": max(0, PHASE_0_TARGET - len(songs)),
    }


# ---------------------------------------------------------------------------
# 4. CLI 入口
# ---------------------------------------------------------------------------
def _parse_args(argv: List[str]) -> Dict[str, Any]:
    """极简 CLI:--batch <name|all> + --output <path>"""
    out: Dict[str, Any] = {"batch": "seed_10", "output": None}
    i = 1
    while i < len(argv):
        a = argv[i]
        if a == "--batch" and i + 1 < len(argv):
            out["batch"] = argv[i + 1]
            i += 2
        elif a == "--output" and i + 1 < len(argv):
            out["output"] = argv[i + 1]
            i += 2
        else:
            i += 1
    return out


def main() -> int:
    args = _parse_args(sys.argv)
    batch_arg = args["batch"]
    output_path = args["output"]
    try:
        if batch_arg == "all":
            data = load_all(list(BATCHES.keys()))
        elif batch_arg in BATCHES:
            data = load_batch(batch_arg)
        else:
            print(f"[ERROR] 未知 batch: {batch_arg},可选: {list(BATCHES.keys()) + ['all']}", file=sys.stderr)
            return 1
    except (FileNotFoundError, ValueError) as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 1
    summary = summarize(data)
    summary_text = json.dumps(summary, ensure_ascii=False, indent=2)
    if output_path is not None:
        p = Path(output_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(summary_text + "\n", encoding="utf-8")
        print(f"[OK] summary 已写入 {p}({len(summary_text)} 字节 · {summary['total_songs']} 首)")
    else:
        print(summary_text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
