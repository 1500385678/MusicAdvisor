#!/usr/bin/env python3
"""
MusicAdvisor LLM 乐理问答基线评估脚手架 v0
=========================================

> 19-音乐-Music · 任务 9 · 2026-09-12 T5 起步
> Phase 0 收官 9/13 任务 9 LLM 乐理问答基线评估 v0

**作用**:
- 加载 `questions.json` 题库(默认 9 题 v0 起步)
- 调用 LLM provider(可替换:minimax / claude / qwen-music)对每题做问答
- 与标准答案对比打 0/1 分
- 输出 baseline JSON + 准确率分布

**v0 用法**:
    # 用 MiniMax M3(本 19-音乐 agent)跑 baseline
    python3 eval_runner.py --provider minimax --model MiniMax-M3 \\
        --questions questions.json --output baseline_v0.json

**Phase 1 续做(双模型)**:
    # Claude API(需 ANTHROPIC_API_KEY 环境变量)
    export ANTHROPIC_API_KEY=sk-ant-...
    python3 eval_runner.py --provider claude --model claude-3-5-sonnet \\
        --questions questions.json --output baseline_v1_claude.json

    # Qwen-Music(需 DASHSCOPE_API_KEY 环境变量)
    export DASHSCOPE_API_KEY=sk-...
    python3 eval_runner.py --provider qwen --model qwen-music-turbo \\
        --questions questions.json --output baseline_v1_qwen.json

**输出格式**:
    {
      "meta": { provider, model, question_count, ... },
      "results": [
        {"id": "Q-01", "question": "...", "answer": "...", "expected": "...",
         "correct": 1, "scoring_type": "exact_match", "latency_ms": 1234}
      ],
      "summary": {
        "total": 9, "correct": 7, "accuracy": 0.778,
        "by_difficulty": {"L1_音程": {"total": 3, "correct": 3, "acc": 1.0}, ...}
      }
    }
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


# ---------------------------------------------------------------------------
# 答案评分函数
# ---------------------------------------------------------------------------

def score_answer(result: Dict[str, Any], question: Dict[str, Any]) -> int:
    """根据 question.scoring.type 评 0/1 分。"""
    scoring = question.get("scoring", {})
    s_type = scoring.get("type", "exact_match")
    answer = (result.get("answer") or "").strip()
    if not answer:
        return 0

    expected = question.get("answer", {})
    primary = expected.get("primary")
    aliases = expected.get("alias", [])

    if s_type == "exact_match":
        accept_any = scoring.get("accept_any_alias", True)
        candidates = [primary] + (aliases if accept_any else [])
        return 1 if any(_match_text(answer, c) for c in candidates if c) else 0

    if s_type == "sequence_match":
        # 主答案为列表/字符串,要求按顺序匹配
        if isinstance(primary, list):
            return 1 if _sequence_match(answer, primary) else 0
        # 字符串序列(如 "Dm-G7-Cmaj7")
        return 1 if _match_text(answer, primary) else 0

    if s_type == "set_match":
        # 无序集合匹配
        if isinstance(primary, list):
            return 1 if _set_match(answer, primary) else 0
        return 1 if _match_text(answer, primary) else 0

    return 0


def _match_text(haystack: str, needle: Any) -> bool:
    """大小写不敏感 + 去空格 + 标点宽松匹配。"""
    if needle is None:
        return False
    n = _norm(str(needle))
    h = _norm(haystack)
    return n in h or h in n


def _norm(s: str) -> str:
    """大小写不敏感 + 去空格/标点/连字符 + 保留字母数字和 #。

    这样 "Dm - G7 - Cmaj7" / "Dm-G7-Cmaj7" / "Dm G7 Cmaj7" 标准化后都是 "dmg7cmaj7",
    "C# maj7" 和 "C#maj7" 都是 "c#maj7"。
    """
    return "".join(ch for ch in s.lower() if ch.isalnum() or ch == "#")


def _sequence_match(answer: str, expected: List[str]) -> bool:
    """按顺序匹配所有 expected 项(用 - / 空格 / 逗号 分隔)。"""
    a = _norm(answer)
    cursor = 0
    for item in expected:
        n = _norm(item)
        idx = a.find(n, cursor)
        if idx < 0:
            return False
        cursor = idx + len(n)
    return True


def _set_match(answer: str, expected: List[str]) -> bool:
    """集合匹配:expected 所有元素都在 answer 中(顺序无关)。"""
    a = _norm(answer)
    return all(_norm(item) in a for item in expected)


# ---------------------------------------------------------------------------
# LLM provider 抽象
# ---------------------------------------------------------------------------

def call_minimax(question: Dict[str, Any], model: str = "MiniMax-M3") -> str:
    """调 MiniMax M3 直接回答(默认当前 agent 的模型)。

    Phase 1 续做可改为通过 mavis / minimax-api 调远端 API。
    """
    # v0 起步:让外部调用者传入预生成的答案(via --answer-map JSON)
    # 或留空让 LLM 在外部(本 agent 自身)答完再写入 JSON
    raise NotImplementedError(
        "v0 起步: MiniMax M3 baseline 由本 19-音乐 agent 直接在对话中作答,"
        "答案手动写入 baseline_v0.json(避免在 cron 中递归调 LLM)。"
        "Phase 1 续做: 用 mavis session send 调子 agent 跑 30 题自动评估。"
    )


def call_claude(question: Dict[str, Any], model: str = "claude-3-5-sonnet-20241022") -> str:
    """调 Claude API(需 ANTHROPIC_API_KEY)。"""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY 未设置,无法调 Claude API。")
    # Phase 1 续做:用 anthropic SDK
    try:
        import anthropic  # type: ignore
    except ImportError:
        raise RuntimeError("请先 pip install anthropic 后再调 Claude。")
    client = anthropic.Anthropic(api_key=api_key)
    prompt = _build_prompt(question)
    msg = client.messages.create(
        model=model,
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text.strip()


def call_qwen(question: Dict[str, Any], model: str = "qwen-music-turbo") -> str:
    """调 Qwen-Music / 通义千问 API(需 DASHSCOPE_API_KEY)。"""
    api_key = os.environ.get("DASHSCOPE_API_KEY")
    if not api_key:
        raise RuntimeError("DASHSCOPE_API_KEY 未设置,无法调 Qwen。")
    try:
        import dashscope  # type: ignore
    except ImportError:
        raise RuntimeError("请先 pip install dashscope 后再调 Qwen。")
    from dashscope import Generation
    prompt = _build_prompt(question)
    resp = Generation.call(
        model=model,
        prompt=prompt,
        api_key=api_key,
        result_format="message",
    )
    if resp.status_code != 200:
        raise RuntimeError(f"Qwen API error: {resp.code} {resp.message}")
    return resp.output.choices[0].message.content.strip()


PROVIDERS: Dict[str, Callable[[Dict[str, Any], str], str]] = {
    "minimax": call_minimax,
    "claude": call_claude,
    "qwen": call_qwen,
}


def _build_prompt(question: Dict[str, Any]) -> str:
    """构造中文 prompt(对齐飞书 Agent 真实交互风格)。"""
    q = question["question"]
    hint = question.get("hint", "")
    return (
        "你是 MusicAdvisor 音乐顾问,精通乐理。"
        "请用简短准确的中文回答以下乐理问题,只回答答案本体,不要解释过程。\n\n"
        f"问题: {q}\n"
        f"提示: {hint}\n\n"
        "答案:"
    )


# ---------------------------------------------------------------------------
# 主入口
# ---------------------------------------------------------------------------

def run_eval(
    questions_path: Path,
    provider: str,
    model: str,
    output_path: Path,
    answer_map: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """跑评估,返回 baseline dict(同时写盘)。"""
    with questions_path.open(encoding="utf-8") as f:
        qd = json.load(f)
    questions = qd["questions"]

    caller = PROVIDERS.get(provider)
    if caller is None:
        raise ValueError(f"Unknown provider: {provider},可选: {list(PROVIDERS.keys())}")

    results: List[Dict[str, Any]] = []
    for q in questions:
        t0 = time.time()
        if answer_map and q["id"] in answer_map:
            # v0 模式:从外部传入答案
            answer = answer_map[q["id"]]
            err = None
        else:
            try:
                answer = caller(q, model=model)
                err = None
            except Exception as e:  # noqa: BLE001
                answer = ""
                err = str(e)
        latency = int((time.time() - t0) * 1000)

        result = {
            "id": q["id"],
            "difficulty": q.get("difficulty", ""),
            "topic": q.get("topic", ""),
            "question": q["question"],
            "answer": answer,
            "expected": q.get("answer", {}).get("primary"),
            "expected_aliases": q.get("answer", {}).get("alias", []),
            "scoring_type": q.get("scoring", {}).get("type", "exact_match"),
            "latency_ms": latency,
            "error": err,
        }
        result["correct"] = score_answer({"answer": answer}, q)
        results.append(result)

    # 汇总
    by_diff: Dict[str, Dict[str, int]] = {}
    for r in results:
        d = r["difficulty"]
        if d not in by_diff:
            by_diff[d] = {"total": 0, "correct": 0}
        by_diff[d]["total"] += 1
        by_diff[d]["correct"] += int(r["correct"])
    for d, v in by_diff.items():
        v["acc"] = round(v["correct"] / v["total"], 3) if v["total"] else 0.0

    total = len(results)
    correct = sum(int(r["correct"]) for r in results)
    summary = {
        "total": total,
        "correct": correct,
        "accuracy": round(correct / total, 3) if total else 0.0,
        "by_difficulty": by_diff,
    }

    baseline = {
        "meta": {
            "name": "MusicAdvisor LLM 乐理问答基线",
            "provider": provider,
            "model": model,
            "question_count": total,
            "questions_file": str(questions_path),
            "created": time.strftime("%Y-%m-%d %H:%M:%S"),
        },
        "results": results,
        "summary": summary,
    }
    output_path.write_text(
        json.dumps(baseline, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return baseline


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--questions", type=Path, default=Path(__file__).parent / "questions.json",
                   help="题库 JSON 路径(默认 questions.json)")
    p.add_argument("--provider", default="minimax", choices=list(PROVIDERS.keys()),
                   help="LLM provider: minimax(默认/v0) / claude / qwen")
    p.add_argument("--model", default="MiniMax-M3", help="模型名(默认 MiniMax-M3)")
    p.add_argument("--output", type=Path, default=Path(__file__).parent / "baseline.json",
                   help="输出 baseline JSON 路径(默认 baseline.json)")
    p.add_argument("--answer-map", type=Path, default=None,
                   help="v0 模式:外部传入答案 JSON {Q-01: 'answer', ...},避免 cron 中递归调 LLM")
    args = p.parse_args()

    answer_map = None
    if args.answer_map:
        answer_map = json.loads(args.answer_map.read_text(encoding="utf-8"))

    baseline = run_eval(
        questions_path=args.questions,
        provider=args.provider,
        model=args.model,
        output_path=args.output,
        answer_map=answer_map,
    )
    s = baseline["summary"]
    print(f"✅ 评估完成:{args.provider}/{args.model}")
    print(f"   总题数:{s['total']} · 答对:{s['correct']} · 准确率:{s['accuracy']:.1%}")
    for d, v in s["by_difficulty"].items():
        print(f"   {d}:{v['correct']}/{v['total']} = {v['acc']:.1%}")
    print(f"   输出:{args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
