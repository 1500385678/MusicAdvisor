"""乐理问答飞书机器人 · Phase 1 §6 第 1 项目录骨架(2026-09-14 T5 落地)

公开 API:
- create_app: 构造 FastAPI 应用(需 pip install fastapi)
- handle_music_theory_question: 乐理问答核心 handler(无外部依赖)
- PianoVisualizer: 钢琴键 SVG 渲染器(无外部依赖)
- LLMClient: 多 provider LLM 客户端(无外部依赖)

落地节奏:
- v0(本期): 目录骨架 + 路由 + handler 形状 + 钢琴渲染雏形(7 白键 1 八度)
- v1(Phase 1 9/15 ~ 9/20): 真实飞书 app_id 接入 + LLM 真调用 + 88 键全键盘
- v2(Phase 1 9/21 ~ 9/30): 题目库扩 100 题 + RAG 增强 + 错误反馈
"""
from app.feishu_bot.handlers.music_theory import handle_music_theory_question
from app.feishu_bot.llm_client import LLMClient
from app.feishu_bot.piano_visualizer import PianoVisualizer

# create_app 依赖 fastapi(可选依赖),延迟 import 避免 v0 骨架强依赖
try:
    from app.feishu_bot.main import create_app
    _HAS_APP = True
except ImportError:
    create_app = None  # type: ignore[assignment]
    _HAS_APP = False

__all__ = [
    "create_app",
    "handle_music_theory_question",
    "LLMClient",
    "PianoVisualizer",
]
__version__ = "0.1.0"
