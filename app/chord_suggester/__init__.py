"""和弦进行建议器 Web 版 · Phase 1 §6 第 2 项目录骨架(2026-09-15 T5 落地)

公开 API(纯 Python,无需 Node.js):
- suggest_progressions: 5-8 候选和弦进行算法核心(调性 + 情绪 → 进行列表)
- EmotionMapper: 情绪关键词 → 和弦偏好映射(8 档)
- KeyNormalizer: 24 调(C/Am/G/Em 等)归一化 + Roman Numeral
- audio_playback_js: Tone.js 试听函数(JS 源码字符串,Web 端嵌入)

Web 端契约:
- page.template.tsx: Next.js 14 主页面(调性 + 情绪输入 + 候选列表 + 试听)
- api_suggest.template.ts: Next.js API 路由(/api/suggest POST)

落地节奏:
- v0(本期 9/15): 目录骨架 + 候选算法 + 情绪映射 + 调性归一化 + Tone.js 试听契约 + 8 用例
- v1(Phase 1 9/16 ~ 9/20): Next.js 项目真跑(npm install + npm run dev)+ 试听真出声
- v2(Phase 1 9/21 ~ 9/27): 候选扩 30+ 经典进行 + 用户自定义 + 替换功能 + 候选标记"AI 建议"
"""
from app.chord_suggester.chord_progressions import suggest_progressions, PROGRESSIONS_LIBRARY
from app.chord_suggester.emotion_keyword import EmotionMapper, EMOTION_KEYWORDS
from app.chord_suggester.key_normalize import KeyNormalizer, SUPPORTED_KEYS

# audio_playback_js 是 JS 源码字符串,延迟加载避免 Python 包误解析
from app.chord_suggester.audio_playback import audio_playback_js

__all__ = [
    "suggest_progressions",
    "PROGRESSIONS_LIBRARY",
    "EmotionMapper",
    "EMOTION_KEYWORDS",
    "KeyNormalizer",
    "SUPPORTED_KEYS",
    "audio_playback_js",
]
__version__ = "0.1.0"