// page.template.tsx · Next.js 14 App Router 主页面契约
// 用法:Phase 1 v1(9/16 ~ 9/20)用 `npx create-next-app@14` 生成项目后
//      把本文件内容贴入 src/app/page.tsx 即可跑通。
//
// 依赖:Tone.js 14.x(运行时动态 import,避免 SSR 报错)
//
// 布局:
//   ┌────────────────────────────────┐
//   │  调性: [C ▼]  情绪: [happy ▼]  │
//   │  [生成和弦进行]   数量: [5-8]   │
//   ├────────────────────────────────┤
//   │ 候选 1: Pop Anthem             │
//   │ I - V - vi - IV  ▶ 试听        │
//   │ 流行金曲标配...                 │
//   ├────────────────────────────────┤
//   │ 候选 2: ...                    │
//   └────────────────────────────────┘

'use client';

import { useState } from 'react';

const KEYS = ['C','D','E','F','G','A','B','C#','D#','F#','G#','A#',
               'Am','Dm','Em','Fm','Gm','Bm','Cm','C#m','D#m','F#m','G#m','A#m'];
const EMOTIONS = [
  { id: 'happy', label: '快乐', bpm: '100-140' },
  { id: 'sad', label: '忧伤', bpm: '60-90' },
  { id: 'tense', label: '紧张', bpm: '110-150' },
  { id: 'calm', label: '平静', bpm: '60-80' },
  { id: 'epic', label: '史诗', bpm: '90-120' },
  { id: 'tender', label: '温柔', bpm: '70-100' },
  { id: 'mysterious', label: '神秘', bpm: '80-110' },
  { id: 'jazzy', label: '爵士', bpm: '90-130' },
];

interface Candidate {
  id: string;
  name: string;
  roman: string[];
  description: string;
  emotion_score: number;
  key: string;
  is_minor: boolean;
}

export default function HomePage() {
  const [keyChoice, setKeyChoice] = useState('C');
  const [emotion, setEmotion] = useState('happy');
  const [count, setCount] = useState(6);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSuggest() {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/suggest', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ key: keyChoice, emotion, n: count }),
      });
      if (!res.ok) throw new Error(`API error: ${res.status}`);
      const data = await res.json();
      setCandidates(data.candidates || []);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  async function onPlay(c: Candidate) {
    // Phase 1 v1 真接:把 audio_playback.py 的 JS 拷到 lib/ 下,这里动态 import
    // Phase 1 v0 骨架:仅打印
    console.log('play', c.roman, c.key);
  }

  return (
    <main style={{ padding: '24px', fontFamily: 'system-ui, sans-serif' }}>
      <h1>MusicAdvisor · 和弦进行建议器</h1>
      <p style={{ color: '#666' }}>Phase 1 §6 第 2 项 · v0 骨架</p>

      <section style={{ display: 'flex', gap: '12px', alignItems: 'center', margin: '16px 0' }}>
        <label>调性
          <select value={keyChoice} onChange={e => setKeyChoice(e.target.value)} style={{ marginLeft: 4 }}>
            {KEYS.map(k => <option key={k} value={k}>{k}</option>)}
          </select>
        </label>
        <label>情绪
          <select value={emotion} onChange={e => setEmotion(e.target.value)} style={{ marginLeft: 4 }}>
            {EMOTIONS.map(e => <option key={e.id} value={e.id}>{e.label} ({e.bpm} BPM)</option>)}
          </select>
        </label>
        <label>数量
          <input type="number" min={5} max={8} value={count}
                 onChange={e => setCount(Number(e.target.value))} style={{ width: 60, marginLeft: 4 }} />
        </label>
        <button onClick={onSuggest} disabled={loading}
                style={{ padding: '8px 16px', background: '#3b82f6', color: 'white', border: 'none', borderRadius: 6 }}>
          {loading ? '生成中…' : '生成和弦进行'}
        </button>
      </section>

      {error && <p style={{ color: 'red' }}>错误: {error}</p>}

      <section>
        {candidates.length === 0 && !loading && (
          <p style={{ color: '#999' }}>点击"生成和弦进行"查看 5-8 个候选(基于情绪权重排序)</p>
        )}
        {candidates.map((c, i) => (
          <article key={c.id} style={{ border: '1px solid #e5e7eb', borderRadius: 8, padding: 12, margin: '8px 0' }}>
            <h3 style={{ margin: '0 0 8px 0' }}>候选 {i+1}: {c.name}</h3>
            <p style={{ margin: '4px 0', fontFamily: 'monospace', fontSize: 16 }}>
              {c.roman.join(' → ')}
            </p>
            <p style={{ margin: '4px 0', color: '#666' }}>{c.description}</p>
            <p style={{ margin: '4px 0', fontSize: 12, color: '#999' }}>
              情绪匹配度: {(c.emotion_score * 100).toFixed(0)}% · 调性: {c.key}
            </p>
            <button onClick={() => onPlay(c)}
                    style={{ padding: '4px 12px', background: '#10b981', color: 'white', border: 'none', borderRadius: 4 }}>
              ▶ 试听
            </button>
          </article>
        ))}
      </section>
    </main>
  );
}