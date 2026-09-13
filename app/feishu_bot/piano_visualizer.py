"""钢琴键 SVG 渲染器
from __future__ import annotations
(9/14 v0 骨架:1 八度 7 白键 + 5 黑键)

输出:Markdown 内嵌 SVG 字符串,可直接贴飞书消息卡片
Phase 1 9/15 扩展:88 键全键盘 + 标红高亮 + 滚屏
"""
from __future__ import annotations

# 1 八度 = 7 白键 + 5 黑键
_WHITE_KEYS = ["C", "D", "E", "F", "G", "A", "B"]
# 黑键位置(白键索引 → 黑键名) 1=C# 2=D# 4=F# 5=G# 6=A#
_BLACK_KEY_OFFSETS = {1: "C#", 2: "D#", 4: "F#", 5: "G#", 6: "A#"}


class PianoVisualizer:
    """1 八度钢琴键 SVG 渲染器(本期 v0)"""

    def __init__(self, width: int = 350, height: int = 100):
        self.width = width
        self.height = height
        self.white_count = len(_WHITE_KEYS)
        self.white_w = width // self.white_count
        self.white_h = height

    def render(self, highlight: list[str] | None = None) -> str:
        """渲染 1 八度 SVG,可选高亮音(白键名 C/D/E/F/G/A/B)"""
        hl = set(highlight or [])
        whites_svg = []
        for i, name in enumerate(_WHITE_KEYS):
            x = i * self.white_w
            fill = "#ff6b6b" if name in hl else "#ffffff"
            stroke = "#333"
            whites_svg.append(
                f'<rect x="{x}" y="0" width="{self.white_w}" height="{self.white_h}" '
                f'fill="{fill}" stroke="{stroke}"/>'
                f'<text x="{x + self.white_w // 2}" y="{self.white_h - 8}" '
                f'font-size="10" text-anchor="middle" fill="#333">{name}</text>'
            )
        # 黑键简化:在 C# / D# / F# / G# / A# 位置叠加
        blacks = [("C#", 1), ("D#", 2), ("F#", 4), ("G#", 5), ("A#", 6)]
        blacks_svg = []
        bw = self.white_w // 2
        bh = self.white_h * 2 // 3
        for name, wi in blacks:
            x = wi * self.white_w - bw // 2
            blacks_svg.append(
                f'<rect x="{x}" y="0" width="{bw}" height="{bh}" '
                f'fill="#222" stroke="#000"/>'
            )
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.width}" '
            f'height="{self.height}" viewBox="0 0 {self.width} {self.height}">'
            + "".join(whites_svg)
            + "".join(blacks_svg)
            + "</svg>"
        )
        return svg
