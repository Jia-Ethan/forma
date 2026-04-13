# SC-TH 质量清单 v2

当前清单只对应 Word 主线。

## 前端

- 极简首页只保留单入口，不再出现旧 workspace 信息结构
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

## 导出结果

- 返回 `.docx`
- 文档内包含目录字段
- 题目、摘要、正文、参考文献至少可见
- 模板缺失时返回明确错误，而不是 500 栈输出

## 当前自动检查

- `npm run build --prefix web`
- `npm run test:smoke --prefix web`
- `uv run pytest tests -q`
- `python3 scripts/build_web_public.py`
