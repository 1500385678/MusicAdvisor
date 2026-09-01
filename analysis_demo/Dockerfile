# MusicAdvisor · Phase 1 后端 FastAPI 起步 Dockerfile
#
# 角色:Phase 0/1 起步基建(9/1 巡检 P1 项),为 Phase 1 真实模式准备可复现的容器环境
# 目标:`docker build -t musicadvisor-analysis .` + `docker run` 跑通 librosa + essentia 4 维输出契约
# 关联:`项目开发计划.md` §5 Phase 0 · §6 Phase 1 任务3 音频分析 MVP
# 配套:`analysis_demo/requirements.txt`(已锁 librosa 0.10.x / essentia 2.1b6 / numpy 1.26.x)
# 创建:2026-09-02 · T5 03:00

# ---- 1. 基础镜像 ----
# 选 python:3.11-slim:Phase 1 FastAPI 起步兼容,numpy 1.26 / librosa 0.10 官方支持,
# 比 alpine 少踩 musl 编译坑(essentia wheel 在 musl 段不稳)
FROM python:3.11-slim AS base

# 元数据(OCI 标准)
LABEL maintainer="19-音乐-Music 行业顾问 <architectzy@users.noreply.github.com>"
LABEL project="MusicAdvisor"
LABEL phase="Phase-0/1-起步基建"
LABEL description="MusicAdvisor 音频分析 demo · FastAPI 起步容器"

# 防止 .pyc 写入 + 强制 stdout 日志
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# ---- 2. 系统依赖 ----
# essentia 需要 ffmpeg 链接 + libsndfile;librosa 需要 libsndfile 读 WAV
# 不装 gcc / build-essential:Phase 0 demo 跑官方 wheel 即可,源码编译留 Phase 2
RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg \
        libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# ---- 3. 工作目录 ----
WORKDIR /app

# ---- 4. Python 依赖(分层缓存) ----
# 先 COPY requirements 单独成层,代码变更不触发 pip 重装
COPY requirements.txt /app/analysis_demo/requirements.txt
RUN pip install --no-cache-dir -r /app/analysis_demo/requirements.txt

# ---- 5. 源码复制 ----
COPY librosa_quicklook.py /app/analysis_demo/librosa_quicklook.py
COPY README.md /app/analysis_demo/README.md

# ---- 6. 入口占位 ----
# Phase 0 demo 仍以 CLI 调用为主(librosa_quicklook.py),FastAPI 服务留 Phase 1 接入
# 此处 ENTRYPOINT 保持 CLI,CMD 跑占位模式让 `docker run` 不报 "no command"
WORKDIR /app/analysis_demo
ENTRYPOINT ["python3", "librosa_quicklook.py"]
CMD []

# ---- 7. 健康检查(Phase 1 接入 FastAPI 后再启) ----
# HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
#     CMD python3 -c "import librosa, essentia" || exit 1

# ---- 8. 变更记录 ----
# 2026-09-02 · T5 03:00 创建 · 9/1 巡检 P1 项 · Phase 1 后端 FastAPI 起步基建
#   - 选 python:3.11-slim(非 alpine,避开 musl)
#   - 系统依赖 ffmpeg + libsndfile1(essentia + librosa 必需)
#   - 分层 COPY requirements,代码变更不触发 pip 重装
#   - 入口暂用 CLI,FastAPI 服务留 Phase 1
