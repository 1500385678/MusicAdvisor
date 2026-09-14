// api_suggest.template.ts · Next.js 14 App Router API 路由契约
// 用法:Phase 1 v1 接入后,放到 src/app/api/suggest/route.ts
//
// 端点:POST /api/suggest
// 请求:{ key: "C"|"Am"|..., emotion: "happy"|"sad"|..., n: 5-8 }
// 响应:{ candidates: [...], meta: { key, emotion, n, generated_at } }
//
// Phase 1 v0:调用 Python 候选算法(由 Next.js 后端 RPC);v1:算法可迁到 TS

import { NextRequest, NextResponse } from 'next/server';
import { suggest_progressions } from '@/lib/chord_progressions';  // 假设算法迁到 TS

const VALID_EMOTIONS = ['happy', 'sad', 'tense', 'calm', 'epic', 'tender', 'mysterious', 'jazzy'];

export async function POST(req: NextRequest) {
  let body: any;
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: 'invalid JSON body' }, { status: 400 });
  }

  const { key, emotion, n } = body;

  // 1. 校验输入
  if (!key || typeof key !== 'string') {
    return NextResponse.json({ error: 'key is required (string)' }, { status: 400 });
  }
  if (!emotion || !VALID_EMOTIONS.includes(emotion)) {
    return NextResponse.json({ error: `emotion must be one of ${VALID_EMOTIONS.join('/')}` }, { status: 400 });
  }
  if (!n || n < 5 || n > 8) {
    return NextResponse.json({ error: 'n must be in [5, 8]' }, { status: 400 });
  }

  // 2. 调 Python 候选算法(Phase 1 v0 走 RPC,v1 迁 TS 后省掉)
  // const rpcRes = await fetch(`${process.env.PY_BACKEND}/suggest`, { ... });
  // const candidates = await rpcRes.json();
  // v1 直跑:
  const candidates = suggest_progressions(key, emotion, n);

  // 3. 响应
  return NextResponse.json({
    candidates,
    meta: {
      key,
      emotion,
      n,
      generated_at: new Date().toISOString(),
      note: 'AI 建议,非乐谱,可人工修正',
    },
  });
}

export async function GET() {
  return NextResponse.json({
    info: 'POST { key, emotion, n:5-8 }',
    valid_emotions: VALID_EMOTIONS,
  });
}