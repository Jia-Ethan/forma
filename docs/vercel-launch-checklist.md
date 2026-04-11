# Vercel Launch Checklist

## 文档一致性

- [x] `README.md` 已改为线上主文档
- [x] `README-local.md` 只描述本地开发与本地 PDF
- [x] `docs/deploy-vercel.md` 与实际部署步骤一致
- [x] 首页支持边界与 README 描述一致

## 本地开发

- [x] `uv sync` 可完成 Python 依赖安装
- [x] `npm install --prefix web` 可完成前端依赖安装
- [x] 本地后端可启动
- [x] 本地前端可启动
- [x] 本地开发模式可完成 `.docx` 主流程
- [x] 本地开发模式可完成“粘贴正文”主流程
- [x] 本地开发模式可导出 `.tex` zip
- [x] 本地开发模式下，若启用 PDF，可导出 PDF

## vercel dev

- [x] `vercel dev` 可本地跑通同一路由结构
- [x] `/api/health` 正常返回 capability flags
- [x] 静态前端可访问
- [x] `.docx` 上传主流程可完成
- [x] 粘贴文本主流程可完成

备注：

- 已确认旧问题不是业务逻辑错误，而是本机默认 `python3` 仍为 3.9 时，Vercel 本地 Python runtime 会启动失败。
- 显式把 `uv` 管理的 Python 3.12 加到 `PATH` 前面后，`vercel dev` 已可正常跑通 API 与静态页面。

## Vercel 预览环境

- [x] preview URL 可访问：`https://scnu-thesis-portal-git-feat-vercel-l-e3191b-jia-ethans-projects.vercel.app`
- [x] 首页展示支持范围与不支持范围
- [x] 上传 `.docx` 后可通过 `/api/parse/docx` 看到识别结果
- [x] 粘贴正文后可通过 `/api/normalize/text` 看到识别结果
- [x] 用户可在网页内修正字段
- [x] `.tex` zip 可下载：补全 metadata 后 `/api/export/texzip` 返回 `200 application/zip`
- [x] 生产环境 PDF 按钮默认隐藏，接口明确返回 `PDF_DISABLED`
- [x] 错误提示清楚，不出现裸 `500`：非 `.docx` 返回 `UNSUPPORTED_FILE_TYPE`，缺封面字段返回 `FIELD_MISSING`

补充实测：

- Vercel 项目最初启用了 SSO protection，公开访问返回 `401`；已关闭该项目 preview SSO protection 后完成公开验收。
- 根级 FastAPI 入口会接管站点路由，因此构建脚本会生成 `backend/app/frontend_bundle.py`，让前端 HTML/CSS/JS 随 Python Function 一起部署。
- 预览环境没有 XeLaTeX 与相关宏包，符合首轮“生产默认关闭 PDF，仅导出 `.tex` zip”的边界。

## 测试

- [x] pytest 全通过
- [x] 前端 smoke test 通过
- [x] 手工验收记录已补充到文档或 PR 描述
