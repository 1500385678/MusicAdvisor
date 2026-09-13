"""飞书机器人配置(从 env 读取)"""
from __future__ import annotations
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """飞书 app + LLM provider 配置"""
    feishu_app_id: str = ""
    feishu_app_secret: str = ""
    feishu_verification_token: str = ""
    feishu_encrypt_key: str = ""
    llm_provider: str = "minimax"  # minimax | claude | qwen


def load_settings() -> Settings:
    """从环境变量读;本期 env 全空,使用默认值即可(目录骨架不需要真接入)"""
    return Settings(
        feishu_app_id=os.getenv("FEISHU_APP_ID", ""),
        feishu_app_secret=os.getenv("FEISHU_APP_SECRET", ""),
        feishu_verification_token=os.getenv("FEISHU_VERIFICATION_TOKEN", ""),
        feishu_encrypt_key=os.getenv("FEISHU_ENCRYPT_KEY", ""),
        llm_provider=os.getenv("LLM_PROVIDER", "minimax"),
    )
