# Deploy to Vercel

## 目标架构

- 一个 Vercel 项目
- 根级 `public/` 提供静态前端
- 根级 `index.py` 提供 Python FastAPI 接口，`/api/*` rewrite 到该入口
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

当前仓库的 Python 运行时基线为 `3.12`。Vercel 云端会按仓库配置安装依赖；本地 `vercel dev` 则会受你机器上 `python3` 默认版本影响。

## 本地模拟 Vercel

在执行前，请先确保前端构建产物已经同步到 `public/`：

```bash
cd /Users/ethan/scnu-thesis-portal
python3 scripts/build_web_public.py
PATH="$(dirname "$(uv python find 3.12)"):$PATH" vercel dev
```

如果你的系统 `python3` 仍指向 3.9 或更低，本地 Python Function 可能会因为解释器版本不匹配而无法启动；优先用上面的 `PATH` 方式显式切到 `uv` 管理的 3.12。

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
- 不把服务器文件系统当作持久状态
