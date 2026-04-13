# Deploy to Vercel

## 目标架构

- 一个 Vercel 项目
- 构建阶段将 `web/dist` 同步到根级 `public/`
- 根级 `index.py` 暴露 Python FastAPI 应用
- 因当前不使用 Vercel Services，FastAPI 在根路径提供 `public/index.html`，并在 `/assets/*` 提供前端静态资源
- `/api/*` 保持为结构化解析、标准化与导出接口
- `scripts/build_web_public.py` 会额外生成 `backend/app/frontend_bundle.py`，把首轮前端构建产物打进 Python 函数包；该文件是构建产物，不入库
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

Vercel 当前会把 FastAPI 项目的 Install Command 识别为：

```bash
pip install -r requirements.txt
```

因此仓库根目录保留 `requirements.txt` 作为 Vercel 云端安装入口；本地开发仍优先使用 `uv sync --extra dev`。

## 预览部署

```bash
cd /Users/ethan/scnu-thesis-portal
vercel
```

当前仓库的 Python 运行时基线为 `3.12`。Vercel 云端会按仓库配置安装依赖；本地 `vercel dev` 则会受你机器上 `python3` 默认版本影响。

当前预览地址：

- https://scnu-thesis-portal-git-feat-vercel-l-e3191b-jia-ethans-projects.vercel.app

如果预览环境出现 SSO 登录页，需要在 Vercel 项目中关闭 preview deployment 的 SSO protection，或提供 bypass 链接后再验收。

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
- Vercel 打包通过 `.vercelignore` 排除上游模板、历史输出和临时目录；生产导出只依赖 `templates/working/latex-scnu-web/`
