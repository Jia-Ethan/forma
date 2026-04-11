# 本地开发说明

> 本文件只描述本地开发和本地演示方式。当前产品主线以线上同步解析、网页 review / 修正、导出 `.tex` 工程 zip 为准；历史 job polling demo 不再作为主路径。

## 1. 安装依赖

```bash
cd /Users/ethan/scnu-thesis-portal
uv sync --extra dev
npm install --prefix web
```

## 2. 启动后端

```bash
cd /Users/ethan/scnu-thesis-portal
uv run uvicorn backend.app.main:app --reload --port 8000
```

## 3. 启动前端

```bash
cd /Users/ethan/scnu-thesis-portal
npm run dev --prefix web
```

## 4. 生成静态前端并模拟 Vercel

```bash
cd /Users/ethan/scnu-thesis-portal
uv run python scripts/generate_frontend_types.py
python3 scripts/build_web_public.py
PATH="$(dirname "$(uv python find 3.12)"):$PATH" vercel dev
```

如果本机默认 `python3` 仍是 3.9 或更低，`vercel dev` 的 Python Function 本地启动会失败。当前仓库已经锁定到 Python 3.12，因此本地模拟时建议显式把 `uv` 管理的 3.12 放到 `PATH` 前面。

## 5. 本地 PDF 能力

本地环境默认允许尝试导出 PDF，但前提是：

- 已安装 `xelatex`
- 已安装 `kpsewhich`
- TeX 宏包至少包含 `ctex`、`titlesec`、`titletoc`

如需明确关闭本地 PDF：

```bash
export ENABLE_PDF_EXPORT=0
```

如需保留调试产物：

```bash
export SCNU_DEBUG_PERSIST_ARTIFACTS=1
```

## 6. 本地验收

```bash
cd /Users/ethan/scnu-thesis-portal
uv run pytest tests -q
npm run test:smoke --prefix web
```
