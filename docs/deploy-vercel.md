# Vercel 与 Workbench 部署说明

当前 Vercel 生产环境适合部署 SCNU 本科论文 Word 快速导出主线。Workbench v1 涉及数据库、对象存储、worker 和私有 Provider 配置，更适合 Docker Compose 或私有服务器部署。

## Vercel 构建链

- `buildCommand`：`npm ci --prefix web && uv run python scripts/build_web_public.py`
- `outputDirectory`：`public`
- API 入口：`/index`

## Vercel 生产依赖

- `backend/`
- `web/`
- `templates/working/sc-th-word/`
- `scripts/generate_frontend_types.py`
- `scripts/build_web_public.py`
- `scripts/check_docx_compliance.py`

## Vercel 部署后验收

1. 首页输入与预检可用
2. `.docx` 上传和文本输入都可走通
3. 可导出 `.docx`
4. 下载结果通过 `uv run python scripts/check_docx_compliance.py`
5. 抽查正式封面、目录、页眉页脚和页码

## Workbench 自托管

Workbench 推荐使用仓库根目录的 `docker-compose.yml`：

```bash
docker compose up --build
```

服务包括：

- `web`：Vite React 工作台
- `api`：FastAPI 文档解析、Workbench API 和导出
- `worker`：后续 Celery/Redis job 入口，占位进程已存在
- `postgres`：项目、版本、Proposal、Agent events 等结构化数据
- `redis`：长任务队列预留
- `minio`：对象存储预留

关键环境变量：

- `SCNU_DATABASE_URL`：默认本地 SQLite；Compose 使用 Postgres
- `SCNU_STORAGE_DIR`：默认 `outputs/storage`
- `SCNU_ACCESS_CODE`：启用私有部署访问码保护
- `SCNU_SECRET_KEY`：用于服务端封存 Provider key
- `VITE_API_BASE_URL`：前端访问 API 的地址
- `CORS_ALLOWED_ORIGINS`：前端源白名单

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
