# SC-TH 质量清单 v2

本清单保留作为轻量入口，并同步 Workbench v1 骨架。

## 入口与预检

- 首页维持极简输入壳层，不额外扩展主视觉
- 预检弹窗一次性展示阻塞项 / 警告项 / 信息项
- 缺失章节说明为“保留留白位”，不再使用“必须补足后才能继续”的旧口径
- 默认主入口不暴露正文自动写入路径
- Story2Paper 实验输出不得直接进入可导出正文版本

## Workbench

- 可创建项目并上传文件
- 项目创建向导默认本地优先，并显示远程 Provider 授权提示
- 项目设置可修改写作阶段、隐私模式和远程授权
- 文件记录包含类型、hash、storage key、parser、source label
- 解析任务生成 baseline version、Issue Ledger、Agent events
- Proposal 默认 pending，接受前不影响当前导出版本
- 接受影响导出的 Proposal 时必须创建新版本
- 删除项目后原始文件和导出文件不可继续访问
- Source Guardian 未确认来源不得影响合规结论

## 导出结果

- 产物为规范化 `.docx`
- Markdown 和自检报告可从 Workbench 导出
- PDF 当前允许降级保留 `.docx` 并记录状态
- 正式封面进入主线第一页
- 目录为 Word 字段
- 页眉页脚、页码与分节规则稳定

## 安全

- Provider key 不返回前端
- Provider 设置页只显示 `has_api_key`、模型、base URL 和验证状态
- 配置 `SCNU_ACCESS_CODE` 时，未验证请求必须被 API 拒绝
- 自定义 base URL 默认拒绝内网、本机、link-local 和保留地址
- Ollama 本地地址必须显式允许
- 日志和 Agent event 不应存储原始正文全文作为调试输出

## 自动检查

- `uv run pytest tests -q`
- `npm run test:smoke --prefix web`
- `npm run build --prefix web`
- `uv run python scripts/build_web_public.py`
- `uv run python scripts/export_compliance_fixture.py tmp/fixture-export.docx`
- `uv run python scripts/check_docx_compliance.py tmp/fixture-export.docx`
