"""飞书乐理问答机器人 · FastAPI 入口

启动方式(Phase 1 9/15 ~ 9/20 接入真 app_id 后):
    uvicorn app.feishu_bot.main:app --host 0.0.0.0 --port 8000

环境变量(本期不读,留空):
- FEISHU_APP_ID
- FEISHU_APP_SECRET
- FEISHU_VERIFICATION_TOKEN
- FEISHU_ENCRYPT_KEY(可选)
- LLM_PROVIDER(minimax|claude|qwen,默认 minimax)
"""
from __future__ import annotations
from typing import Optional
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse

from app.feishu_bot.config import Settings, load_settings
from app.feishu_bot.handlers.music_theory import handle_music_theory_question


def create_app(settings: Optional[Settings] = None) -> FastAPI:
    """构造 FastAPI 应用;settings 为 None 时从 env 读(本期留空,默认行为)"""
    cfg = settings or load_settings()
    app = FastAPI(
        title="MusicAdvisor · 乐理问答飞书机器人",
        version="0.1.0",
        description="Phase 1 §6 第 1 项 · 9/14 T5 目录骨架落地",
    )
    app.state.settings = cfg

    @app.get("/healthz")
    async def healthz():
        return {"status": "ok", "version": app.version}

    @app.post("/feishu/webhook")
    async def feishu_webhook(request: Request):
        """飞书事件回调入口(URL 验证 + 消息接收)"""
        body = await request.json()
        # 1. URL 验证(challenge 字段)
        if body.get("type") == "url_verification":
            return JSONResponse({"challenge": body.get("challenge", "")})
        # 2. 消息事件(Phase 1 9/15 接入真 app_id 后做签名校验)
        try:
            return await _dispatch_event(body, cfg)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    return app


async def _dispatch_event(body: dict, cfg: Settings) -> dict:
    """事件分发(本期仅占位,Phase 1 9/15 接入真事件订阅)"""
    header = body.get("header", {})
    event_type = header.get("event_type", "")
    event = body.get("event", {})
    # 仅处理文本消息中的乐理问答
    if event_type == "im.message.receive_v1":
        msg = event.get("message", {})
        msg_type = msg.get("message_type", "")
        if msg_type == "text":
            text = _extract_text(msg.get("content", "{}"))
            answer = handle_music_theory_question(text, llm_provider=cfg.llm_provider)
            return {"answer": answer, "phase": "v0-skeleton"}
    return {"answer": "暂未处理", "phase": "v0-skeleton"}


def _extract_text(content_json: str) -> str:
    """从飞书 content JSON 串里取纯文本"""
    import json
    try:
        return json.loads(content_json).get("text", "").strip()
    except Exception:
        return ""


# 默认 app(uvicorn 直接挂载)
app = create_app()
