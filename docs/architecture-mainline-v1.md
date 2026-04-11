# Architecture Mainline v1

## 唯一主线

当前项目唯一主线是：

用户上传 `.docx` 或粘贴文字 -> 后端解析为 normalized thesis schema -> 用户在网页内 review / 修正 -> 导出规范化 `.tex` 工程 zip。

这条主线以 `feat/vercel-launch-v1` / PR #1 为基线继续推进。`main` 上的后台线程 job 模式只作为历史本地 MVP 记录，不再作为产品路径。

## 运行模式

- 开发模式：前端使用 Vite dev server，后端使用 FastAPI；前端通过 `/api/*` 调用后端。
- 本地演示模式：构建前端后由 FastAPI 提供页面和 API，可按需开启本地 PDF 导出。
- 线上预览模式：部署到 Vercel，主产物为 `.tex` 工程 zip；PDF 默认关闭，并返回 `PDF_DISABLED`。

生产环境不依赖 `outputs/jobs`、`tmp/jobs`、后台线程、任务轮询或长期本地文件状态。

## 主路径接口

- `GET /api/health`：返回服务状态、能力开关、上传限制和 TeX 环境探测结果。
- `POST /api/parse/docx`：接收 `.docx`，返回 normalized thesis schema。
- `POST /api/normalize/text`：接收粘贴文本，返回 normalized thesis schema。
- `POST /api/export/texzip`：接收 normalized thesis schema，返回 `.tex` 工程 zip。
- `POST /api/export/pdf`：仅本地或显式 feature flag 开启时可用；线上默认返回 `PDF_DISABLED`。

前后端契约以后端 Pydantic schema 为源，生成 TypeScript 类型供前端使用，避免维护两套同等地位的 schema。

## 数据流

1. 用户选择 `.docx` 上传或粘贴文本。
2. 后端只抽取文本、标题层级和可识别结构，不保留 Word 原始样式。
3. 前端展示摘要、Abstract、正文、参考文献、致谢、附录和封面字段。
4. 用户在 review 页面补全和修正字段。
5. 后端复制 `templates/working/latex-scnu-web/` 到请求级临时目录，写入生成的 `.tex` 文件。
6. 后端把工作目录打包为 zip 并直接返回，不把服务器文件系统当作持久状态。

## 保留与降级

保留：

- `templates/upstream/`：上游模板来源和授权 / 差异参考。
- `templates/working/latex-scnu-web/`：当前唯一生产导出工作模板。
- `.docx` 解析、文本 normalize、texzip export、本地 PDF 编译服务。
- `docs/local-mvp-*`：历史阶段记录。

降级或淘汰：

- 后台线程 job 模式。
- `/api/jobs/*` 旧任务接口。
- `/jobs/:jobId` 轮询状态页。
- `outputs/jobs`、`tmp/jobs` 作为主状态来源。
- 任何暗示线上稳定生成 PDF 或一键修复 Word 格式的文案。

## 当前边界

- 仅支持 `.docx`，不支持 `.doc`。
- 不保留原 Word 样式。
- 不承诺复杂表格、图片、脚注、特殊排版完整恢复。
- 不承诺学校官方规范已经逐条核验。
- 不引入数据库、对象存储、队列或重后端。
- Vercel 首轮上线使用 FastAPI frontend bundle fallback 提供页面；后续如切换到 Vercel Services 或独立静态托管，再拆分前端静态资源与 Python API。
