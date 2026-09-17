"""MIDI 批量入库脚手架 · Phase 1 §6 第 4 项续做。

v0 骨架:Phase 1 续做 100+ / 1000+ / 1 万 + MIDI 真实入库时使用,提供:

    1. 单条 schema 校验(ST-XX / MO-XX / TP-XX / KY-XX 4 维 + 字段完整性)
    2. 批校验 + 聚合错误(批量拒绝而非首错即停)
    3. 追加写入 index_meta.json + 自动更新 _meta.created_at + _meta.batch_id + 覆盖度统计
    4. CLI 入口:`python -m app.midi_library.batch_loader --input batch.json [--dry-run]`
    5. next_id 自动生成(M-XXX 末尾递进)

设计要点:
    - 不直接绑死 .mid 二进制文件(版权风险,见 项目开发计划.md §8)
    - 字段最小可入库:沿用 MidiMetadata dataclass + index_meta.json schema
    - 错误聚合:每条错误带 index + id 方便定位,不要静默吃掉
    - dry_run 默认 True,先校验后真写,避免误操作
    - Phase 1 续做:接 mido/pretty_midi 真链路后,本模块扩展为 .mid → metadata 自动抽取 → 校验入库

契约源:`analysis_demo/scores/midi_tags_v0.json` v0 4 维标签字典
    (ST-XX 16 / MO-XX 8 / TP-XX 5 / KY-XX 24)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Sequence

from app.midi_library.midi_loader import MidiMetadata


# ============================================================================
# 错误聚合 + 单条 schema 校验
# ============================================================================

@dataclass
class BatchValidationError:
    """单条入库错误(行号 + id + 字段 + 原因)。"""

    line_no: int          # 在 batch JSON 数组中的下标(从 1 起)
    midi_id: str          # 报错的 MIDI id(可能为空)
    field: str            # 出错的字段名
    reason: str           # 错误原因

    def to_dict(self) -> Dict:
        return {
            "line_no": self.line_no,
            "id": self.midi_id,
            "field": self.field,
            "reason": self.reason,
        }


# 4 维标签字典合法范围(沿用 midi_tags_v0 契约)
_VALID_STYLE = {f"ST-{i:02d}" for i in range(1, 17)}                # ST-01 ~ ST-16
_VALID_MOOD = {f"MO-{i:02d}" for i in range(1, 9)}                  # MO-01 ~ MO-08
_VALID_TEMPO = {f"TP-{i:02d}" for i in range(1, 6)}                 # TP-01 ~ TP-05
_VALID_KEY = {f"KY-{i:02d}" for i in range(1, 25)}                  # KY-01 ~ KY-24
_ID_RE = re.compile(r"^M-(\d{3,})$")                                  # M-001 ~ M-999+
_BPM_RANGE = (1, 300)
_DURATION_MIN = 1


def _parse_id_num(midi_id: str) -> Optional[int]:
    """从 M-XXX 字符串解析出末尾数字;不合法返回 None。"""
    if not midi_id:
        return None
    m = _ID_RE.match(midi_id.strip())
    if not m:
        return None
    return int(m.group(1))


def _prefix_ok(value: str, codes: set) -> bool:
    """判断 value 是否以 codes 任一前缀开头(如 'ST-01 流行' 以 'ST-01' 起)。"""
    if not value:
        return False
    for code in codes:
        if value.startswith(code):
            return True
    return False


def validate_entry(
    entry: Dict,
    existing_ids: Sequence[str],
) -> List[BatchValidationError]:
    """单条 schema 校验。失败返回 1+ 条错误,成功返回空列表。

    Args:
        entry: 候选条目 dict(从 JSON 读取)。
        existing_ids: 现有 index_meta.json 中已存在的 id 列表,用于查重。

    Returns:
        错误列表;为空表示通过。
    """
    errors: List[BatchValidationError] = []
    midi_id = str(entry.get("id", "")).strip()

    # 1. id 格式 M-XXX
    if not midi_id:
        errors.append(BatchValidationError(0, midi_id, "id", "id 不能为空"))
    elif _parse_id_num(midi_id) is None:
        errors.append(
            BatchValidationError(0, midi_id, "id", "id 格式不合法,期望 M-XXX(M + 横线 + 3+ 位数字)")
        )
    elif midi_id in set(existing_ids):
        errors.append(BatchValidationError(0, midi_id, "id", f"id 已存在({midi_id})"))

    # 2. title 非空
    title = str(entry.get("title", "")).strip()
    if not title:
        errors.append(BatchValidationError(0, midi_id, "title", "title 不能为空"))

    # 3. style_primary ST-XX
    style = str(entry.get("style_primary", "")).strip()
    if not style:
        errors.append(BatchValidationError(0, midi_id, "style_primary", "style_primary 不能为空"))
    elif not _prefix_ok(style, _VALID_STYLE):
        errors.append(
            BatchValidationError(0, midi_id, "style_primary",
                                 f"style_primary 不在 ST-01 ~ ST-16 范围,实际: {style!r}")
        )

    # 4. mood MO-XX(可为空列表但每项需合法)
    mood = entry.get("mood", [])
    if not isinstance(mood, list):
        errors.append(BatchValidationError(0, midi_id, "mood", "mood 必须是列表"))
    else:
        for i, m in enumerate(mood):
            if not _prefix_ok(str(m), _VALID_MOOD):
                errors.append(
                    BatchValidationError(0, midi_id, f"mood[{i}]",
                                         f"mood[{i}] 不在 MO-01 ~ MO-08 范围,实际: {m!r}")
                )

    # 5. tempo TP-XX
    tempo = str(entry.get("tempo", "")).strip()
    if not tempo:
        errors.append(BatchValidationError(0, midi_id, "tempo", "tempo 不能为空"))
    elif not _prefix_ok(tempo, _VALID_TEMPO):
        errors.append(
            BatchValidationError(0, midi_id, "tempo",
                                 f"tempo 不在 TP-01 ~ TP-05 范围,实际: {tempo!r}")
        )

    # 6. key KY-XX
    key = str(entry.get("key", "")).strip()
    if not key:
        errors.append(BatchValidationError(0, midi_id, "key", "key 不能为空"))
    elif not _prefix_ok(key, _VALID_KEY):
        errors.append(
            BatchValidationError(0, midi_id, "key",
                                 f"key 不在 KY-01 ~ KY-24 范围,实际: {key!r}")
        )

    # 7. bpm 数值合法
    bpm_raw = entry.get("bpm", 0)
    try:
        bpm = int(bpm_raw)
    except (TypeError, ValueError):
        errors.append(BatchValidationError(0, midi_id, "bpm", f"bpm 不是整数,实际: {bpm_raw!r}"))
        bpm = 0
    if not (_BPM_RANGE[0] <= bpm <= _BPM_RANGE[1]):
        errors.append(
            BatchValidationError(0, midi_id, "bpm",
                                 f"bpm 超出 {_BPM_RANGE[0]} ~ {_BPM_RANGE[1]} 范围,实际: {bpm}")
        )

    # 8. duration_sec >= 1
    duration_raw = entry.get("duration_sec", 0)
    try:
        duration_sec = int(duration_raw)
    except (TypeError, ValueError):
        errors.append(BatchValidationError(0, midi_id, "duration_sec",
                                           f"duration_sec 不是整数,实际: {duration_raw!r}"))
        duration_sec = 0
    if duration_sec < _DURATION_MIN:
        errors.append(
            BatchValidationError(0, midi_id, "duration_sec",
                                 f"duration_sec 必须 >= {_DURATION_MIN},实际: {duration_sec}")
        )

    # 9. tags 列表 + tag_count_total 一致
    tags = entry.get("tags", [])
    if not isinstance(tags, list):
        errors.append(BatchValidationError(0, midi_id, "tags", "tags 必须是列表"))
    else:
        tct_raw = entry.get("tag_count_total", 0)
        try:
            tct = int(tct_raw)
        except (TypeError, ValueError):
            errors.append(BatchValidationError(0, midi_id, "tag_count_total",
                                               f"tag_count_total 不是整数,实际: {tct_raw!r}"))
            tct = 0
        if tct != len(tags):
            errors.append(
                BatchValidationError(0, midi_id, "tag_count_total",
                                     f"tag_count_total({tct}) 与 len(tags)({len(tags)}) 不一致")
            )

    # 10. 必填文本字段非空
    for field_name in ("style_subtag", "scale", "time_signature"):
        val = str(entry.get(field_name, "")).strip()
        if not val:
            errors.append(BatchValidationError(0, midi_id, field_name, f"{field_name} 不能为空"))

    return errors


# ============================================================================
# 批校验 + 追加 + CLI
# ============================================================================

@dataclass
class BatchValidationReport:
    """批校验聚合报告。"""

    total: int                  # 输入条目数
    passed: int                 # 通过条数
    failed: int                 # 失败条数
    errors: List[BatchValidationError]   # 失败详情

    def is_all_pass(self) -> bool:
        return self.failed == 0

    def to_dict(self) -> Dict:
        return {
            "total": self.total,
            "passed": self.passed,
            "failed": self.failed,
            "errors": [e.to_dict() for e in self.errors],
        }


def validate_batch(
    entries: Sequence[Dict],
    existing_ids: Sequence[str],
) -> BatchValidationReport:
    """批量校验 entries。

    Args:
        entries: 待校验条目列表。
        existing_ids: 现有 id 列表。

    Returns:
        BatchValidationReport(含每条错误的行号 + id + field)。
    """
    errors: List[BatchValidationError] = []
    seen_ids: set = set()
    passed = 0
    for i, entry in enumerate(entries, start=1):
        line_no = i
        # batch 内查重
        local_id = str(entry.get("id", "")).strip()
        if local_id and local_id in seen_ids:
            errors.append(
                BatchValidationError(line_no, local_id, "id",
                                     f"id 在当前 batch 内重复({local_id})")
            )
            continue
        if local_id:
            seen_ids.add(local_id)

        per_errs = validate_entry(entry, existing_ids)
        # 把 line_no 填上
        for e in per_errs:
            e.line_no = line_no
        errors.extend(per_errs)
        if not per_errs:
            passed += 1
    return BatchValidationReport(
        total=len(entries),
        passed=passed,
        failed=len(entries) - passed,
        errors=errors,
    )


def next_id(prefix: str, existing_ids: Sequence[str]) -> str:
    """生成下一个 ID。

    Args:
        prefix: 前缀(如 "M-")。
        existing_ids: 现有 id 列表。

    Returns:
        新的 ID(如 "M-011")。
    """
    max_num = 0
    for eid in existing_ids:
        n = _parse_id_num(str(eid))
        if n is not None and n > max_num:
            max_num = n
    return f"{prefix}{max_num + 1:03d}"


def _load_index(index_path: Path) -> Dict:
    """读取 index_meta.json(不存在返回空 dict 结构)。"""
    if not index_path.exists():
        return {"_meta": {}, "entries": []}
    with index_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if "entries" not in data:
        data["entries"] = []
    if "_meta" not in data:
        data["_meta"] = {}
    return data


def _cover_stats(entries: List[Dict]) -> Dict[str, int]:
    """统计 entries 在 4 维标签上的覆盖度。"""
    styles: set = set()
    moods: set = set()
    tempos: set = set()
    keys: set = set()
    for e in entries:
        sp = str(e.get("style_primary", "")).strip()
        for code in _VALID_STYLE:
            if sp.startswith(code):
                styles.add(code)
                break
        for m in e.get("mood", []):
            for code in _VALID_MOOD:
                if str(m).startswith(code):
                    moods.add(code)
                    break
        for code in _VALID_TEMPO:
            if str(e.get("tempo", "")).startswith(code):
                tempos.add(code)
                break
        for code in _VALID_KEY:
            if str(e.get("key", "")).startswith(code):
                keys.add(code)
                break
    return {
        "style_count": len(styles),
        "mood_count": len(moods),
        "tempo_count": len(tempos),
        "key_count": len(keys),
    }


def append_batch(
    entries: Sequence[Dict],
    index_path: Path,
    *,
    batch_id: Optional[str] = None,
    dry_run: bool = True,
) -> BatchValidationReport:
    """追加一批 entries 到 index_meta.json。

    Args:
        entries: 待写入条目列表。
        index_path: index_meta.json 路径。
        batch_id: 批次标识(如 "2026-09-18-batch-01");None 时自动生成。
        dry_run: True 仅校验不写,False 真写。

    Returns:
        BatchValidationReport(失败时不写入)。
    """
    data = _load_index(index_path)
    existing_ids = [e.get("id", "") for e in data.get("entries", []) if e.get("id")]
    report = validate_batch(entries, existing_ids)

    if not report.is_all_pass():
        return report

    if dry_run:
        return report

    # 真写
    new_entries = list(data.get("entries", []))
    new_entries.extend(entries)

    meta = data.get("_meta", {})
    meta["last_batch_id"] = batch_id or f"batch-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    meta["last_batch_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    meta["last_batch_size"] = len(entries)
    meta["total_entries"] = len(new_entries)
    meta["last_batch_coverage"] = _cover_stats(new_entries)
    data["_meta"] = meta
    data["entries"] = new_entries

    with index_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    return report


def load_batch_json(path: Path) -> List[Dict]:
    """从 JSON 文件加载待入库条目(支持顶层数组或 {entries:[...]} 结构)。"""
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "entries" in data:
        return data["entries"]
    raise ValueError(
        f"batch JSON 顶层必须是数组或包含 entries 字段,实际: {type(data).__name__}"
    )


def _default_index_path() -> Path:
    return Path(__file__).resolve().parent / "index_meta.json"


def _cli(argv: Optional[List[str]] = None) -> int:
    """CLI 入口:`python -m app.midi_library.batch_loader --input batch.json [--commit]`。"""
    parser = argparse.ArgumentParser(
        description="MIDI 批量入库脚手架 · dry_run 默认开启,加 --commit 真写。"
    )
    parser.add_argument("--input", "-i", required=True, help="待入库 JSON 文件路径")
    parser.add_argument(
        "--index", default=str(_default_index_path()), help="index_meta.json 路径"
    )
    parser.add_argument(
        "--batch-id", default=None, help="批次 ID(如 2026-09-18-batch-01)"
    )
    parser.add_argument(
        "--commit", action="store_true",
        help="真写入(默认 dry_run,仅校验不写)",
    )
    args = parser.parse_args(argv)

    entries = load_batch_json(Path(args.input))
    report = append_batch(
        entries,
        Path(args.index),
        batch_id=args.batch_id,
        dry_run=not args.commit,
    )
    summary = report.to_dict()
    mode = "COMMIT" if args.commit else "DRY_RUN"
    print(f"[{mode}] total={summary['total']} passed={summary['passed']} "
          f"failed={summary['failed']}")
    if report.errors:
        print("[ERRORS]")
        for e in summary["errors"]:
            print(f"  line={e['line_no']} id={e['id']!r} field={e['field']} reason={e['reason']}")
    return 0 if report.is_all_pass() else 1


if __name__ == "__main__":
    sys.exit(_cli())