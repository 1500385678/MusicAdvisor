// Next.js 14 API 路由契约 · 接收音频上传 → 返回 AnalysisReport JSON
// Phase 1 §6 第 3 项 v0 骨架 · 路径: app/audio_analysis/api_analyze.template.ts
//
// 使用方式(Phase 1 真实接入):
//   1. 复制本文件到 ../../../app/api/audio/analyze/route.ts
//   2. 取消 mock 段注释,启用后端 Python 调用
//   3. 当前端 fetch('/api/audio/analyze', { method: 'POST', body: formData }) 时触发
//
// 输入:multipart/form-data,字段 'file' = audio binary (.mp3 / .wav / ...)
// 输出:JSON AnalysisReport(含可视化 PNG Base64)

import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export const runtime = 'nodejs'          // 需要 Node.js runtime(File / Buffer)
export const dynamic = 'force-dynamic'   // 禁用静态优化,每次请求都跑
export const maxDuration = 30            // 秒 · 上传 + 分析总时间上限

/**
 * POST /api/audio/analyze
 * Body: multipart/form-data { file: File }
 * Returns: AnalysisReport JSON
 */
export async function POST(request: NextRequest) {
  try {
    // 1. 解析上传
    const formData = await request.formData()
    const file = formData.get('file')

    if (!file || !(file instanceof File)) {
      return NextResponse.json(
        { error: '缺少音频文件(字段 file)' },
        { status: 400 }
      )
    }

    // 2. 格式校验(支持 MP3/WAV/FLAC/OGG/M4A)
    const validExts = ['.mp3', '.wav', '.flac', '.ogg', '.m4a']
    const fileName = (file as File).name
    const ext = fileName.slice(fileName.lastIndexOf('.')).toLowerCase()
    if (!validExts.includes(ext)) {
      return NextResponse.json(
        { error: `不支持的音频格式: ${ext}(支持: ${validExts.join('/')})` },
        { status: 415 }
      )
    }

    // 3. 大小限制(默认 50MB,Phase 1 可调)
    const MAX_SIZE = 50 * 1024 * 1024
    if (file.size > MAX_SIZE) {
      return NextResponse.json(
        { error: `文件过大: ${(file.size / 1024 / 1024).toFixed(1)}MB > ${MAX_SIZE / 1024 / 1024}MB` },
        { status: 413 }
      )
    }

    // ===== Phase 1 v0 骨架 mock 段 =====
    // 当前返回 mock 报告,Phase 1 续做替换为真实后端调用
    const mockReport = {
      source_path: fileName,
      duration_sec: 180.5,
      sample_rate: 22050,
      tempo: {
        bpm: 120.0,
        beat_count: 361,
        beat_times: Array.from({ length: 361 }, (_, i) => i * 0.5),
        confidence: 0.92,
        bpm_bucket: 'medium',
      },
      key: {
        key: 'C',
        scale: 'major',
        confidence: 0.85,
        chroma: [0.083, 0.083, 0.083, 0.083, 0.083, 0.083,
                 0.083, 0.083, 0.083, 0.083, 0.083, 0.083],
        top5_candidates: [
          { key: 'C major', score: 0.20 },
          { key: 'G major', score: 0.15 },
          { key: 'F major', score: 0.10 },
          { key: 'Am minor', score: 0.10 },
          { key: 'D minor', score: 0.05 },
        ],
      },
      chords: {
        segments: [
          { start_time: 0.0,  end_time: 45.0, chord: 'C',  confidence: 0.88, duration_sec: 45.0 },
          { start_time: 45.0, end_time: 90.0, chord: 'G',  confidence: 0.85, duration_sec: 45.0 },
          { start_time: 90.0, end_time: 135.0, chord: 'Am', confidence: 0.87, duration_sec: 45.0 },
          { start_time: 135.0, end_time: 180.5, chord: 'F', confidence: 0.82, duration_sec: 45.5 },
        ],
        vocabulary: ['C', 'G', 'Am', 'F'],
        unique_count: 4,
      },
      visualization_png_b64: '', // Phase 1 真渲染时填入
      meta: {
        version: '0.1.0',
        phase: 'Phase 1 §6 第 3 项 v0 目录骨架',
        analyzed_at: new Date().toISOString(),
        tempo_confidence: 0.92,
        key_confidence: 0.85,
        mean_chord_confidence: 0.855,
      },
    }
    return NextResponse.json(mockReport, { status: 200 })

    // ===== Phase 1 真实模式(注释保留) =====
    // const buf = Buffer.from(await file.arrayBuffer())
    // const tmpPath = `/tmp/audio-upload-${Date.now()}${ext}`
    // await writeFile(tmpPath, buf)
    // const { spawn } = require('child_process')
    // const py = spawn('python', [
    //   '-m', 'app.audio_analysis.pipeline',
    //   '--path', tmpPath,
    // ])
    // ... 收集 stdout → JSON.parse → 返回
  } catch (err) {
    console.error('[audio/analyze] error:', err)
    return NextResponse.json(
      { error: '音频分析失败', detail: String(err) },
      { status: 500 }
    )
  }
}

/**
 * GET /api/audio/analyze
 * 健康检查 · 返回服务状态
 */
export async function GET() {
  return NextResponse.json({
    service: 'audio-analysis',
    version: '0.1.0',
    phase: 'Phase 1 §6 第 3 项 v0 目录骨架',
    endpoints: {
      POST: '上传音频 + 返回 AnalysisReport(JSON)',
    },
    supported_formats: ['.mp3', '.wav', '.flac', '.ogg', '.m4a'],
    max_size_mb: 50,
  })
}