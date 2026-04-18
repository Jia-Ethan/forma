# SCNU 本科论文导出实施与验收记录 v1

## 本轮工程调整

- 重建后端中间结构，统一 `.docx` 与文本输入
- 重写预检规则，使缺失章节转为留白警告而非默认阻塞
- 重写 Word 导出器，纳入正式封面、TOC 字段、分节、页眉页脚、页码与显式样式
- 新增 `.docx` 合规检查脚本
- 同步更新 README、规范映射、审计与限制文档

## 当前自动保证

- 正式封面纳入主线第一页
- 缺失字段和缺失章节保留留白位
- 目录为 Word 字段
- 前置部分罗马页码、正文阿拉伯页码
- 页眉主标题固定规则
- 参考文献统一样式与悬挂缩进

## 当前仍需人工复核

- 表格、图片、脚注、文本框、形状与复杂域代码
- 目录更新后的分页结果
- 个别参考文献条目的格式细节

## 验收记录

- 自动化测试：
  - `uv run pytest tests -q` 通过
  - `npm run test:smoke --prefix web` 通过
  - `npm run build --prefix web` 通过
  - `uv run python scripts/build_web_public.py` 通过
- 合规脚本：
  - `sample-export.docx`：`PASS`
  - `missing-export.docx`：`PASS`
- Git 提交：
  - `81dfa9d Refactor SCNU thesis export mainline`
  - `3a46878 Fix merged compliance compatibility gaps`
  - `4d31402 Record SCNU export rollout results`
- Git 推送：
  - `origin/main -> 3a46878`
  - `origin/main -> 4d31402`
- Vercel 生产部署：
  - 生产构建：`https://scnu-thesis-portal-5qd0y1akw-jia-ethans-projects.vercel.app`
  - 生产别名：`https://scnu-thesis-portal.vercel.app`
  - 健康检查：`GET /api/health` 返回 `{"ok": true, "app_env": "production"}`
