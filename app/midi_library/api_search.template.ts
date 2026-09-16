/**
 * Next.js 14 API 路由契约 · GET /api/midi/search
 *
 * Phase 1 §6 第 4 项「MIDI 素材库最小版」Web 端入口。
 *
 * 路由职责:
 *   1) 解析 query string(bpm、key、mood、style、q/top_k)
 *   2) 转发到后端 FastAPI /api/midi/search(协议见下)
 *   3) 返回结构化 MIDI 候选 + 候选和弦进行
 *   4) 错误兜底 + 健康检查
 *
 * 协议契约(对接 FastAPI Gateway):
 *
 *   Request:
 *     GET /api/midi/search?style=ST-01&mood=MO-02,MO-06&key=KY-13,KY-14
 *         &bpm_min=70&bpm_max=130&q=抒情钢琴&top_k=10
 *
 *   Response 200:
 *     {
 *       "query": { ... },
 *       "matched": [ {id, title, style_primary, bpm, key, ..., match_score} ],
 *       "progressions": { "M-001": [ {name, score, reason}, ... ] },
 *       "meta": { "version", "phase", "indexed_count", "matched_count", "elapsed_ms" }
 *     }
 *
 *   Response 4xx/5xx:
 *     { "error": "INVALID_QUERY", "detail": "bpm_min 必须 ≤ bpm_max", "code": 400 }
 *
 * 不做什么:
 *   - 不缓存(Music v0 骨架无 Redis/Memcached)
 *   - 不鉴权(Phase 1 用户自行调用,Phase 2 加 session)
 *   - 不分页(top_k 限制 ≤ 50)
 *
 * Phase 1 续做:
 *   - 接 FastAPI Gateway /api/midi/search 后端
 *   - 接 NextAuth session 鉴权
 *   - 接 swr / React Query 做前端缓存
 */

import type { NextApiRequest, NextApiResponse } from "next";

interface MidiSearchQuery {
  style: string[];
  mood: string[];
  key: string[];
  bpm_min?: number;
  bpm_max?: number;
  q?: string;
  top_k: number;
}

interface MidiSearchResponse {
  query: Record<string, unknown>;
  matched: Array<{
    id: string;
    title: string;
    style_primary: string;
    bpm: number;
    key: string;
    match_score: number;
    matched_fields: string[];
    snippet: string;
    duration_sec: number;
    tags: string[];
    mood: string[];
    tempo: string;
  }>;
  progressions: Record<string, Array<{ name: string; score: number; reason: string }>>;
  meta: {
    version: string;
    phase: string;
    indexed_count: number;
    matched_count: number;
    elapsed_ms: number;
  };
}

interface MidiSearchError {
  error: string;
  detail: string;
  code: number;
}

// 解析 GET 参数
function parseQuery(req: NextApiRequest): MidiSearchQuery {
  const q = (req.query.q as string) ?? "";
  const style = (req.query.style as string)?.split(",").filter(Boolean) ?? [];
  const mood = (req.query.mood as string)?.split(",").filter(Boolean) ?? [];
  const key = (req.query.key as string)?.split(",").filter(Boolean) ?? [];
  const bpm_min = req.query.bpm_min
    ? parseInt(req.query.bpm_min as string, 10)
    : undefined;
  const bpm_max = req.query.bpm_max
    ? parseInt(req.query.bpm_max as string, 10)
    : undefined;
  const top_k = Math.min(
    Math.max(parseInt((req.query.top_k as string) ?? "20", 10) || 20, 1),
    50,
  );
  return { style, mood, key, bpm_min, bpm_max, q, top_k };
}

// Mock 数据:Phase 1 真实模式替换为 fastapi fetch
function mockSearch(q: MidiSearchQuery): MidiSearchResponse {
  // 演示用:返回 1 条候选 + 1 套和弦进行
  return {
    query: {
      style_codes: q.style,
      mood_codes: q.mood,
      key_codes: q.key,
      bpm_range: q.bpm_min !== undefined && q.bpm_max !== undefined
        ? [q.bpm_min, q.bpm_max]
        : null,
      free_text: q.q,
    },
    matched: [
      {
        id: "M-001",
        title: "Pop Ballad Sketch",
        style_primary: "ST-01 流行",
        bpm: 72,
        key: "KY-14 d minor",
        match_score: 0.95,
        matched_fields: ["mood", "style", "tempo"],
        snippet: "Pop Ballad Sketch · 抒情 · 钢琴 + 弦乐 · 慢板",
        duration_sec: 240,
        tags: ["抒情", "钢琴 + 弦乐", "慢板", "情歌"],
        mood: ["MO-02 忧郁", "MO-06 亲密"],
        tempo: "TP-02 中速",
      },
    ],
    progressions: {
      "M-001": [
        { name: "I-V-vi-IV", score: 0.95, reason: "风格 ST-01 流行 命中 + 情绪命中 1 项" },
        { name: "vi-IV-I-V", score: 0.85, reason: "风格 ST-01 流行 命中 + 情绪命中 1 项" },
        { name: "Pachelbel Canon (I-V-vi-iii-IV)", score: 0.8, reason: "风格 ST-01 流行 命中" },
      ],
    },
    meta: {
      version: "0.1.0",
      phase: "Phase 1 §6 第 4 项 v0 目录骨架",
      indexed_count: 10,
      matched_count: 1,
      elapsed_ms: 12,
    },
  };
}

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse<MidiSearchResponse | MidiSearchError>,
) {
  // 健康检查
  if (req.method === "HEAD") {
    res.status(200).end();
    return;
  }

  if (req.method !== "GET") {
    return res.status(405).json({
      error: "METHOD_NOT_ALLOWED",
      detail: "仅支持 GET / HEAD",
      code: 405,
    });
  }

  try {
    const q = parseQuery(req);

    // BPM 范围合法性
    if (
      q.bpm_min !== undefined &&
      q.bpm_max !== undefined &&
      q.bpm_min > q.bpm_max
    ) {
      return res.status(400).json({
        error: "INVALID_QUERY",
        detail: `bpm_min (${q.bpm_min}) 必须 ≤ bpm_max (${q.bpm_max})`,
        code: 400,
      });
    }

    // 空 query
    const isEmpty =
      q.style.length === 0 &&
      q.mood.length === 0 &&
      q.key.length === 0 &&
      q.bpm_min === undefined &&
      q.bpm_max === undefined &&
      !q.q.trim();
    if (isEmpty) {
      return res.status(400).json({
        error: "EMPTY_QUERY",
        detail: "至少需要 1 个查询条件(style / mood / key / bpm / q)",
        code: 400,
      });
    }

    // Phase 1 真实模式:fetch 到 FastAPI Gateway
    // const backend = process.env.MUSICADVISOR_BACKEND ?? "http://localhost:8000";
    // const r = await fetch(`${backend}/api/midi/search?...`, { method: "GET" });
    // const data = (await r.json()) as MidiSearchResponse;

    // v0 骨架:本地 mock
    const data = mockSearch(q);
    return res.status(200).json(data);
  } catch (err) {
    return res.status(500).json({
      error: "INTERNAL_ERROR",
      detail: err instanceof Error ? err.message : String(err),
      code: 500,
    });
  }
}
