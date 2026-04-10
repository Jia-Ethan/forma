# Deploy to Vercel

## 目标架构

- 一个 Vercel 项目
- 根级 `public/` 提供静态前端
- 根级 `/api/index.py` 提供 Python FastAPI 接口
- 生产环境默认只承诺 `.tex` 工程 zip 导出

## 首次部署

```bash
cd /Users/ethan/scnu-thesis-portal
vercel login
vercel link
```

建议项目名：

- `scnu-thesis-portal`

## 环境变量

生产环境至少需要：

```bash
APP_ENV=production
ENABLE_PDF_EXPORT=0
MAX_DOCX_SIZE_BYTES=4194304
```

如需本地调试落盘：

```bash
SCNU_DEBUG_PERSIST_ARTIFACTS=1
```

## 预览部署

```bash
cd /Users/ethan/scnu-thesis-portal
vercel
```

## 本地模拟 Vercel

在执行前，请先确保前端构建产物已经同步到 `public/`：

```bash
cd /Users/ethan/scnu-thesis-portal
python3 scripts/build_web_public.py
vercel dev
```

## 生产部署

本轮不直接上线正式生产域名。先通过 preview URL 完成验收，再决定是否执行：

```bash
vercel --prod
```

## 回滚

- 通过 Vercel Dashboard 选择上一版 deployment 回滚
- 或重新部署上一版 Git commit

## 当前生产边界

- 支持 `.docx` 上传与文本粘贴
- 支持结构识别、字段补全、预览修正、`.tex` zip 导出
- 默认不启用 PDF
- 不支持 `.doc`
- 不保留原 Word 样式
- 不承诺复杂表格、图片、特殊格式完整恢复
