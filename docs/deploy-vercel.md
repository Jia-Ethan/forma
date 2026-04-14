# Vercel 部署说明

当前生产环境部署的是 SCNU 本科论文 Word 导出主线。

## 构建链

- `buildCommand`：`npm ci --prefix web && python3 scripts/build_web_public.py`
- `outputDirectory`：`public`
- API 入口：`/index`

## 生产依赖

- `backend/`
- `web/`
- `templates/working/sc-th-word/`
- `scripts/generate_frontend_types.py`
- `scripts/build_web_public.py`
- `scripts/check_docx_compliance.py`

## 部署后验收

1. 首页输入与预检可用
2. `.docx` 上传和文本输入都可走通
3. 可导出 `.docx`
4. 下载结果通过 `scripts/check_docx_compliance.py`
5. 抽查正式封面、目录、页眉页脚和页码
