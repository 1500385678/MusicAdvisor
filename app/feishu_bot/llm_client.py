"""LLM client · 多 provider 切换
from __future__ import annotations
(对接 analysis_demo/llm_eval 脚手架)

本期 v0 仅做接口形状,Phase 1 9/15 ~ 9/20 接入真调用。

Provider 优先级(参考 9/12 任务 9 评估结果):
- minimax: 默认,MiniMax M3 在 9 题乐理基线 9/9 = 100% 命中
- claude: 备选,Phase 1 双模型对照
- qwen: 备选,Qwen-Music 中文乐理术语

避免重复造轮子:Phase 1 直接 import analysis_demo/llm_eval/eval_runner.py 的
provider 切换逻辑,本期保留接口形状,后续 import 即可。
"""
from __future__ import annotations
from typing import Literal

Provider = Literal["minimax", "claude", "qwen"]


class LLMClient:
    """LLM 客户端(本期 v0:仅做配置 + 形状;Phase 1 9/15 接入真调用)"""

    def __init__(self, provider: Provider = "minimax", model: str | None = None):
        self.provider = provider
        self.model = model or self._default_model(provider)
        self._client = None  # Phase 1 9/15 真实实例化

    @staticmethod
    def _default_model(provider: Provider) -> str:
        return {
            "minimax": "MiniMax-M3",
            "claude": "claude-3-5-sonnet",
            "qwen": "qwen-music-turbo",
        }[provider]

    def ask(self, prompt: str, system: str = "") -> str:
        """问 LLM 一个乐理问题;本期返回占位,Phase 1 9/15 真调"""
        return (
            f"[LLMClient.v0 占位] provider={self.provider} model={self.model} "
            f"prompt_len={len(prompt)} · Phase 1 9/15 接入真调用"
        )

    def health(self) -> dict:
        return {
            "provider": self.provider,
            "model": self.model,
            "ready": self._client is not None,
        }
