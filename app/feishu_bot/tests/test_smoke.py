"""乐理问答飞书机器人 v0 烟测
from __future__ import annotations
(9/14 T5 落地)

跑法(Phase 1 9/15 起):
    cd /Users/aaron/Mac/Consultant/19-音乐-Music/_MusicLib/MusicWeb
    pip install -r app/feishu_bot/requirements.txt
    pytest app/feishu_bot/tests/test_smoke.py -v

本期 v0 不强依赖外部(无需真飞书 app_id / LLM),目录骨架即闭环。
"""
from app.feishu_bot import (
    create_app,
    handle_music_theory_question,
    LLMClient,
    PianoVisualizer,
)


def test_create_app_healthz():
    app = create_app()
    routes = [r.path for r in app.routes]
    assert "/healthz" in routes
    assert "/feishu/webhook" in routes


def test_handle_music_theory_question_interval():
    out = handle_music_theory_question("什么是大三度?")
    assert "大三度" in out or "未识别" in out  # 宽松断言,v0 骨架


def test_handle_music_theory_question_chord():
    out = handle_music_theory_question("属七和弦怎么构成?")
    assert "属七和弦" in out or "未识别" in out


def test_handle_music_theory_question_mode():
    out = handle_music_theory_question("什么是五声音阶?")
    assert "五声音阶" in out or "未识别" in out


def test_handle_music_theory_question_empty():
    out = handle_music_theory_question("")
    assert "请输入" in out


def test_llm_client_interface():
    c = LLMClient(provider="minimax")
    h = c.health()
    assert h["provider"] == "minimax"
    assert h["ready"] is False  # v0 骨架
    out = c.ask("大三度是什么?")
    assert "占位" in out


def test_piano_visualizer_render():
    pv = PianoVisualizer()
    svg = pv.render(highlight=["C", "E", "G"])
    assert "<svg" in svg
    assert 'fill="#ff6b6b"' in svg  # 高亮
    assert "C" in svg and "E" in svg and "G" in svg


def test_piano_visualizer_no_highlight():
    pv = PianoVisualizer()
    svg = pv.render()
    assert "<svg" in svg
    assert "#ff6b6b" not in svg
