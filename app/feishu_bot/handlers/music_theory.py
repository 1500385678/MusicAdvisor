"""乐理问答 handler
from __future__ import annotations
(音程 / 和弦 / 调式 三档难度)

输入:用户问题文本(飞书消息 text 字段)
输出:Markdown 格式回答 + 钢琴键 SVG(可选)

本期 v0 目录骨架只做:
1. 解析问题(关键词匹配识别类别:音程/和弦/调式)
2. 查 music_theory_lib 的基础数据
3. 调用 LLMClient 拿答案(本期不真调,留接口)
4. 拼装 Markdown 回答(钢琴键 SVG Phase 1 9/15 再加)

Phase 1 9/15 ~ 9/20 续做:
- 飞书真消息接入 + 加签校验
- LLMClient 真调(对接 analysis_demo/llm_eval 脚手架)
- 钢琴键 SVG 真渲染(PianoVisualizer 已有雏形)
"""
from __future__ import annotations
from app.feishu_bot.music_theory_lib import lookup_interval, lookup_chord, lookup_mode
from app.feishu_bot.llm_client import LLMClient


_CATEGORY_KEYWORDS = {
    "interval": ["音程", "多少度", "半音", "全音"],
    "chord": ["和弦", "三和弦", "七和弦", "九和弦", "挂留"],
    "mode": ["调式", "大调", "小调", "五声音阶", "蓝调音阶", "多利安", "mixolydian"],
}


def _classify(question: str) -> str:
    """根据关键词识别问题类别;默认 interval(最多见)"""
    q = question.lower()
    for cat, kws in _CATEGORY_KEYWORDS.items():
        for kw in kws:
            if kw in q:
                return cat
    return "interval"


def handle_music_theory_question(
    question: str,
    llm_provider: str = "minimax",
    use_llm: bool = False,
) -> str:
    """乐理问答入口(本期 v0 骨架:仅走本地知识库;use_llm=False)

    返回:Markdown 文本,Phase 1 9/15 改为飞书消息卡片(含钢琴键 SVG)
    """
    if not question:
        return "请输入乐理问题(音程/和弦/调式三档)。"
    cat = _classify(question)
    if cat == "interval":
        return _answer_interval(question)
    if cat == "chord":
        return _answer_chord(question)
    if cat == "mode":
        return _answer_mode(question)
    return "未识别的问题类别,请使用关键词:音程/和弦/调式。"


def _answer_interval(q: str) -> str:
    """音程类问题:查本地知识库 + 可选 LLM 兜底"""
    # 简化:命中 12 个标准音程名之一即返回
    for name in lookup_interval(""):
        if name in q:
            return f"**{name}**:见 `app/feishu_bot/music_theory_lib.py` 基础数据表。"
    return "本期 v0 骨架仅识别 12 个标准音程名,Phase 1 9/15 接入 LLM 后扩展。"


def _answer_chord(q: str) -> str:
    for name in lookup_chord(""):
        if name in q:
            return f"**{name}**:见 `app/feishu_bot/music_theory_lib.py` 基础数据表。"
    return "本期 v0 骨架仅识别 7 类三和弦/七和弦,Phase 1 9/15 接入 LLM 后扩展。"


def _answer_mode(q: str) -> str:
    for name in lookup_mode(""):
        if name in q:
            return f"**{name}**:见 `app/feishu_bot/music_theory_lib.py` 基础数据表。"
    return "本期 v0 骨架仅识别 7 类调式,Phase 1 9/15 接入 LLM 后扩展。"
