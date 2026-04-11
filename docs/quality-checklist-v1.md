# Quality Checklist v1

## 接口与错误体系

当前主线错误码覆盖：

- `UNSUPPORTED_FILE_TYPE`：上传的不是 `.docx`，或 MIME 类型明显不符合 Word 文档。
- `CONTENT_EMPTY`：上传文件为空，或粘贴文本为空。
- `FILE_TOO_LARGE`：上传文件超过 `MAX_DOCX_SIZE_BYTES`。
- `DOCX_INVALID`：文件扩展名像 `.docx`，但内容不是有效 OOXML zip。
- `PARSE_FAILED`：`.docx` 可进入解析，但无法读取正文结构。
- `FIELD_MISSING`：导出前仍缺少封面、摘要或正文等必填字段。
- `EXPORT_FAILED`：`.tex` 工程或 PDF 导出失败。
- `PDF_DISABLED`：当前环境未开启 PDF 导出。
- `TEMPLATE_DEPENDENCY_MISSING`：工作模板或本地 TeX 依赖缺失。

错误文案面向普通学生，优先说明“哪里不符合”和“下一步怎么处理”，避免只暴露技术异常。

## 安全与边界

已落实：

- 上传大小限制：默认 `4 MB`，由 `MAX_DOCX_SIZE_BYTES` 配置。
- 文件类型校验：同时检查扩展名、MIME 类型和 `.docx` zip magic。
- 临时文件清理：解析、texzip、PDF 生成均使用请求级 `TemporaryDirectory`。
- 路径安全：静态资源 fallback 限制在 `public/assets` 内；texzip 打包跳过 symlink，并校验路径仍位于工作目录内。
- 环境变量分层：`APP_ENV=production` 时默认关闭 PDF；CORS 默认只在开发环境放开本地 Vite origin。
- 运行产物隔离：`outputs/`、`tmp/`、`public/`、`web/dist/`、`backend/app/frontend_bundle.py` 等生成物不作为主仓库内容。

当前边界：

- 不支持 `.doc`。
- 不保留 Word 原始样式。
- 不承诺复杂表格、图片、脚注、特殊排版完整恢复。
- 不承诺线上 PDF 编译。
- 不引入数据库、对象存储、后台队列或用户账号系统。

## 测试覆盖

自动化测试覆盖：

- `GET /api/health` 返回能力开关和上传限制。
- 非 `.docx` 文件被拒绝。
- MIME 类型明显不对的 `.docx` 被拒绝。
- 空 `.docx` 被拒绝。
- 超过大小限制的文件被拒绝。
- 伪 `.docx` 文件被拒绝。
- 损坏 zip 形式的 `.docx` 返回解析失败。
- 合法 `.docx` 可解析为 normalized thesis。
- 粘贴文本可 normalize。
- 空文本被拒绝。
- 缺字段时 texzip 导出返回 `FIELD_MISSING`。
- texzip 可成功导出，并包含生成文件。
- PDF 关闭时返回 `PDF_DISABLED`。
- texzip 打包跳过 symlink，避免把工作目录外文件打进 zip。
- 前端首页 smoke test 通过。

## 本轮验证结果

已执行：

```bash
uv run pytest tests -q
npm run test:smoke --prefix web
PATH="$(dirname "$(uv python find 3.12)"):$PATH" vercel build
npm audit --prefix web --omit=dev --json
```

结果：

- 后端测试：`16 passed`
- 前端 smoke test：`1 passed`
- Vercel build：通过
- 前端生产依赖 audit：`0 vulnerabilities`

第三阶段没有新增产品能力，只补质量护栏。下一阶段可以在这些护栏基础上重写 README 与 GitHub 展示页，不需要再回到本地 job demo 叙事。
