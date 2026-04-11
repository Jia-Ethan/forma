# Iteration Audit v1

## 当前状态摘要

当前仓库存在两条明显不同的实现线：

- `main`：本地 MVP / 历史 demo 主线。
- `feat/vercel-launch-v1` / PR #1：Vercel 首轮上线主线。

`main` 的核心仍是本地异步任务模型：用户提交表单或 `.docx` 后，后端创建 job，后台线程处理，结果落到 `outputs/jobs` 与 `tmp/jobs`，前端通过 `/jobs/:jobId` 轮询状态并下载 PDF / texzip。它适合验证本地编译链路，但不适合作为线上产品主路径。

`feat/vercel-launch-v1` 已经把主流程改成同步 API：上传 `.docx` 或粘贴文本后，后端返回 normalized thesis schema；用户在网页内 review / 修正字段；最终导出规范化 `.tex` 工程 zip。生产环境默认关闭 PDF，并通过 capability flags 与 `PDF_DISABLED` 明确说明。

GitHub 展示层面仍有明显缺口：仓库 About 区的 description、website、topics 尚未整理，latest release 为空；虽然已有 Vercel Preview deployment，但 README 与仓库门面还没有形成稳定的产品型表达。

## 主线建议

后续唯一主线建议采用：

用户上传 `.docx` 或粘贴文字 -> 系统解析为标准化 thesis schema -> 用户在网页内 review / 修正 -> 导出规范化 `.tex` 工程 zip。

这条线应以 `feat/vercel-launch-v1` 为基线继续推进，而不是继续维护 `main` 上的 job polling demo。

原因：

- 更接近真实线上可访问 MVP。
- 不依赖后台线程、长期本地文件目录或 job 轮询。
- 产品体验更符合普通学生使用：先识别，再修正，再导出。
- 能诚实规避线上 PDF 编译不稳定的问题。
- 已有 Vercel Preview deployment，可作为 GitHub 展示与后续迭代入口。

## 需要保留的部分

- `templates/upstream/`：保留为上游模板来源与授权 / 差异参考，不作为主开发区。
- `templates/working/latex-scnu-web/`：保留为当前唯一工作模板。
- `backend/app/contracts.py` 与 `web/src/generated/contracts.ts`：保留为前后端契约主线。
- `.docx` 解析、文本 normalize、texzip export 服务：保留并继续补质量。
- 本地 PDF 编译链路：保留为 local-only 能力，不作为线上承诺。
- `docs/local-mvp-*`、`docs/vercel-launch-*`：保留为阶段记录，但后续 README 主叙事不应再停在历史阶段。

## 需要淘汰或降级的部分

- 后台线程 job 模式：淘汰为主产品路径，仅作为历史方案参考。
- `/api/jobs/from-form`、`/api/jobs/from-docx`、`/api/jobs/{job_id}`、artifact polling / download 这类旧接口：不再作为主线接口。
- `/jobs/:jobId` 任务状态页：不再作为用户主体验。
- `outputs/jobs`、`tmp/jobs` 作为状态来源：不再作为线上主状态。
- README 中“只是 Portal 雏形 / 资料整理仓库”的主叙事：需要在第四阶段改成线上 MVP 产品首页。
- “生成 PDF 与 tex 工程”这类对线上能力有误导的表述：需要统一改为“导出 `.tex` 工程 zip；PDF 仅本地可选”。

## 下一阶段实施范围

第二阶段建议只做工程主线收口，不新增大功能：

- 以 PR #1 / `feat/vercel-launch-v1` 为唯一基线。
- 清理或隔离旧 job polling 相关表达与本地 demo 残留。
- 明确开发模式、本地演示模式、线上预览模式。
- 保持线上主路径为同步解析、review / edit、texzip 导出。
- PDF 继续保持生产默认关闭，错误码与文案保持清楚。
- 输出 `docs/architecture-mainline-v1.md`，说明唯一主线架构。
