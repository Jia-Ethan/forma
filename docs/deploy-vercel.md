# Vercel 与 Workbench 部署说明

Vercel 不再作为主生产站，只保留静态 public mirror / preview。SCNU 本科论文 Word 快速导出和 Workbench 后端需要数据库、临时文件、worker 与访问码保护，应部署到国内云服务器。

## Vercel 构建链

- `buildCommand`：`npm ci --prefix web && python3 scripts/build_web_public.py`
- `outputDirectory`：`public`
- API 入口：无。`vercel.json` 不再 rewrite `/api/*` 到 Python Function。

## Vercel 生产依赖

- `web/`
- `scripts/build_web_public.py`

## Vercel 部署后验收

1. 首页静态内容可打开
2. English 入口可打开
3. Workbench Demo 可交互
4. `/api/*` 不承载真实后端，生产 README 不把 Vercel 作为主站

## Workbench 自托管

Workbench 生产部署推荐使用仓库根目录的 `docker-compose.production.yml`：

```bash
cp .env.production.example .env.production
docker compose --env-file .env.production -f docker-compose.production.yml up -d --build
```

服务包括：

- `web`：Vite React 工作台
- `api`：FastAPI 文档解析、Workbench API 和导出
- `worker`：后续 Celery/Redis job 入口，占位进程已存在
- `postgres`：项目、版本、Proposal、Agent events 等结构化数据
- `caddy`：HTTPS 自动续期与反向代理

关键环境变量：

- `SCNU_DATABASE_URL`：默认本地 SQLite；Compose 使用 Postgres
- `SCNU_STORAGE_DIR`：默认 `outputs/storage`
- `SCNU_ACCESS_CODE`：启用私有部署访问码保护
- `SCNU_SECRET_KEY`：用于服务端封存 Provider key
- `VITE_API_BASE_URL`：前端访问 API 的地址
- `CORS_ALLOWED_ORIGINS`：前端源白名单
- `TURNSTILE_SITE_KEY` / `TURNSTILE_SECRET_KEY`：匿名公开导出的 Turnstile 校验

## Workbench 部署后验收

1. 打开 `/#/workbench`
2. 新建项目
3. 上传 `.docx` 或文本文件
4. 解析后出现 baseline version、Agent events、Issue / Proposal
5. 可生成 Markdown 或自检报告导出记录
6. 删除项目后，导出文件下载地址返回不可访问
7. Provider 配置接口不返回 API key
8. 非 Ollama Provider 的内网 base URL 被拒绝
9. 配置 `SCNU_ACCESS_CODE` 后，未验证请求被拒绝
