# SC-TH 质量清单 v2

本清单保留当前 Word 主线的产品护栏；严格格式合规检查已升级到 [quality-checklist-compliance.md](./quality-checklist-compliance.md)。

## 前端

- 极简首页只保留单入口，不再出现旧 workspace 信息结构
- 首页可见主标题仅为 `SC-TH`
- 首页默认提示为 `按 Cmd/Ctrl + Enter 开始预检`
- 输入框空态保持单行体感，长文本在阈值后切为内部滚动
- 文本模式下 `Enter` 换行，`Cmd/Ctrl + Enter` 触发预检
- 文件与文本输入互斥
- 预检错误落在输入框下方
- 阻塞项存在时确认按钮禁用
- 取消预检后保留当前输入
- 海浪进度只用于导出阶段

## 后端

- `/api/precheck/docx`
- `/api/precheck/text`
- `/api/export/docx`
- `/api/health`
- 导出稿为 `.docx` 正文审查稿，不伪造学校正式封面

## 当前自动检查

- `npm run build --prefix web`
- `npm run test:smoke --prefix web`
- `uv run pytest tests -q`
- `python3 scripts/build_web_public.py`
- `python3 scripts/check_docx_compliance.py /path/to/exported.docx --json`
