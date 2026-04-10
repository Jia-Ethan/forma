# Vercel Launch Checklist

## 文档一致性

- [ ] `README.md` 已改为线上主文档
- [ ] `README-local.md` 只描述本地开发与本地 PDF
- [ ] `docs/deploy-vercel.md` 与实际部署步骤一致
- [ ] 首页支持边界与 README 描述一致

## 本地开发

- [ ] `uv sync` 可完成 Python 依赖安装
- [ ] `npm install --prefix web` 可完成前端依赖安装
- [ ] 本地后端可启动
- [ ] 本地前端可启动
- [ ] 本地开发模式可完成 `.docx` 主流程
- [ ] 本地开发模式可完成“粘贴正文”主流程
- [ ] 本地开发模式可导出 `.tex` zip
- [ ] 本地开发模式下，若启用 PDF，可导出 PDF

## vercel dev

- [ ] `vercel dev` 可本地跑通同一路由结构
- [ ] `/api/health` 正常返回 capability flags
- [ ] 静态前端可访问
- [ ] `.docx` 上传主流程可完成
- [ ] 粘贴文本主流程可完成

## Vercel 预览环境

- [ ] preview URL 可访问
- [ ] 首页展示支持范围与不支持范围
- [ ] 上传 `.docx` 后可看到识别结果
- [ ] 粘贴正文后可看到识别结果
- [ ] 用户可在网页内修正字段
- [ ] `.tex` zip 可下载
- [ ] 生产环境 PDF 按钮默认隐藏，或接口明确返回 `PDF_DISABLED`
- [ ] 错误提示清楚，不出现裸 `500`

## 测试

- [ ] pytest 全通过
- [ ] 前端 smoke test 通过
- [ ] 手工验收记录已补充到文档或 PR 描述
