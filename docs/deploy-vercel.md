# Vercel 部署说明

当前 Vercel 线上主线是 Word 导出版本，不再依赖 LaTeX / PDF 编译。

## 构建链

- `buildCommand`：`npm ci --prefix web && python3 scripts/build_web_public.py`
- `outputDirectory`：`public`
- API 入口：`/index`

前端构建后会写入 `public/`，同时生成 `backend/app/frontend_bundle.py`，供 FastAPI 在 Vercel 环境中直接返回静态资源。

## 生产依赖

线上链路依赖：

- `backend/`
- `web/`
- `templates/working/sc-th-word/`
- `scripts/generate_frontend_types.py`
- `scripts/build_web_public.py`

不再依赖：

- `templates/working/latex-scnu-web/`
- TeX 运行环境
- PDF 编译

## 部署后验收

上线后至少验证：

1. 首页极简输入框加载正常
2. `.docx` 上传可用
3. 文本预检可用
4. 预检弹窗展示阻塞项 / 警告项 / 信息项
5. 通过预检后可自动下载 `.docx`
