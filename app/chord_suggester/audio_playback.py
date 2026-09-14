"""Tone.js 试听函数(JS 源码字符串,Web 端嵌入)

Phase 1 v0 提供骨架契约,Phase 1 v1 (9/16 ~ 9/20) 在 Next.js 项目中真跑。

设计:
- playProgression(romanArray, root, bpm): 顺序播放 4-12 个和弦,每个 1 小节
- 用 Tone.js Sampler 加载 Salamander Grand Piano 音色(CDN)
- 每个和弦 = 同时按下 3 个音(根/三/五/七),用 Tone.PolySynth 简化实现

Python 包导出:
- audio_playback_js: JS 源码字符串常量,供 Next.js page 或 api 路由嵌入
"""
from __future__ import annotations

# Tone.js 试听函数 JS 源码(v0 骨架,v1 接入真实音源)
AUDIO_PLAYBACK_JS = """
// playProgression(romanArray, root, bpm)
// romanArray: ["I", "V", "vi", "IV"] 等
// root: "C", "A" 等(主音)
// bpm: 60-180 整数
// 返回 Promise<void>
async function playProgression(romanArray, root, bpm) {
  // Tone.js 加载(动态 import 避免 SSR 报错)
  if (typeof Tone === 'undefined') {
    await import('https://cdn.jsdelivr.net/npm/tone@14.7.77/build/Tone.min.js');
  }
  Tone.Transport.bpm.value = bpm;

  // 简化:PolySynth 三和弦 + 七和弦
  const synth = new Tone.PolySynth(Tone.Synth, {
    oscillator: { type: 'triangle' },
    envelope: { attack: 0.02, decay: 0.1, sustain: 0.6, release: 0.5 },
  }).toDestination();

  const NOTE_OFFSETS = { 'C': 0, 'C#': 1, 'D': 2, 'D#': 3, 'E': 4, 'F': 5, 'F#': 6, 'G': 7, 'G#': 8, 'A': 9, 'A#': 10, 'B': 11 };
  const QUALITY_BY_DEGREE = {
    'I':   [0, 4, 7],     'i':   [0, 3, 7],
    'II':  [2, 6, 9],     'ii':  [2, 5, 9],
    'III': [4, 8, 11],    'iii': [4, 7, 11],
    'IV':  [5, 9, 12],    'iv':  [5, 8, 12],
    'V':   [7, 11, 14],   'v':   [7, 10, 14],
    'VI':  [9, 13, 16],   'vi':  [9, 12, 16],
    'VII': [11, 14, 17],  'vii': [11, 14, 17],
    'bVII':[10, 14, 17],  'bVI': [8, 12, 15], 'bIII':[3, 7, 10],
  };

  const rootPc = NOTE_OFFSETS[root] ?? 0;
  const baseOctave = 4;
  for (let i = 0; i < romanArray.length; i++) {
    const deg = romanArray[i].replace(/[^IiVv]/g, '');
    const quality = QUALITY_BY_DEGREE[deg] || [0, 4, 7];
    const notes = quality.map(off => {
      const midi = (baseOctave + 1) * 12 + rootPc + off;
      return Tone.Frequency(midi, 'midi').toNote();
    });
    synth.triggerAttackRelease(notes, '1n');
    await new Promise(r => setTimeout(r, (60 / bpm) * 1000));
  }
  synth.dispose();
}

// 导出给 Next.js 使用
if (typeof module !== 'undefined') module.exports = { playProgression };
"""


def audio_playback_js() -> str:
    """返回 Tone.js 试听函数 JS 源码字符串"""
    return AUDIO_PLAYBACK_JS


if __name__ == "__main__":
    # 烟囱测试:打印 JS 源码长度和首行
    js = audio_playback_js()
    print(f"JS length: {len(js)} chars")
    print(f"First line: {js.strip().split(chr(10))[0]}")
    print(f"Has playProgression: {'function playProgression' in js}")
    print(f"Has Tone.PolySynth: {'PolySynth' in js}")