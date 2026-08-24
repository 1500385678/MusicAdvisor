# MusicAdvisor

> 19-音乐-Music 行业 Web 项目 · 内部代号 MusicAdvisor

## 项目说明
基于张勇的 36 行业架构,MusicAdvisor 是 音乐-Music 行业的 Web 端顾问产品。
定位:音乐学习者、创作者、制作人共同的 AI 顾问,做乐理可视化、和弦进行建议、
风格拆解与创作素材库(详见 `项目开发计划.md`)。

## 同步
- GitHub: https://github.com/1500385678/MusicAdvisor
- Gitee: https://gitee.com/architectzy/MusicAdvisor

## 仓库结构
- `项目开发计划.md` — 产品立项 / 阶段计划 / 风险(单一事实源)
- `InspirationIndex.md` — Phase 0 资产盘点索引(乐理/和弦/曲式/风格 四类)
- `.Log/` — 每日巡检报告(T1 02:00 落库)
- `.plan/` — 每日 T5 开发计划(执行后清理)

## 自动化
- T1 每日 02:00 拉 issues · 巡检仓库并写 `.Log/巡检-音乐-YYYYMMDD.md`
- T4 每日 02:00 优化 · 写次日 `.plan/YYYYMMDD.md` 开发计划
- T5 每日 03:00 推 release · 按 plan 完成小步开发并 commit + push
