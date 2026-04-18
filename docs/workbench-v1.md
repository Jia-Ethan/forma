# SCNU Thesis Agent Workbench v1

Workbench v1 是当前仓库的可运行 MVP 骨架，用来把论文材料放进项目空间，并让解析、审查、建议、确认和导出都可追溯。

它不是学校官方系统，也不是论文代写工具。智能辅助只生成候选建议；任何正文相关内容在用户确认前不得进入当前导出版本。

## 当前能力

- 项目空间：创建向导、查询、设置、删除论文项目
- 文件库：上传 `.docx`、PDF、文本、图片/OCR 占位、参考文献文件
- 本地对象存储：默认写入 `outputs/storage`
- 数据层：默认 SQLite，Docker Compose 预留 Postgres
- `NormalizedThesis v2`：block id、source spans、provenance、confidence、comments、format risks
- 版本历史：解析后生成 baseline version，Proposal 接受后可生成新版本
- Issue Ledger：预检 issue 可关联 block、source span、规则来源和建议动作
- Proposal 队列：接受、拒绝、暂存
- Agent events：支持事件列表和 SSE 事件流
- 导出记录：`.docx`、Markdown、自检报告，PDF 当前降级记录
- Provider 配置：OpenAI、Gemini、DeepSeek、MiniMax、Ollama 元数据，服务端密钥保存、验证状态与前端脱敏
- 隐私模式：默认本地优先，远程 Provider 需要项目级显式授权
- 访问码保护：私有部署可通过 `SCNU_ACCESS_CODE` 保护 `/api/*`

## 本地运行

快速开发模式：

```bash
uv sync --extra dev
npm install --prefix web
uv run uvicorn backend.app.main:app --reload --port 8000
VITE_API_BASE_URL=http://127.0.0.1:8000 npm run dev --prefix web
```

访问：

- 快速导出：`http://127.0.0.1:5173/`
- Workbench：`http://127.0.0.1:5173/#/workbench`
- API：`http://127.0.0.1:8000`

自托管骨架：

```bash
docker compose up --build
```

## 核心 API

- `POST /api/projects`
- `GET /api/projects`
- `GET /api/projects/{id}`
- `PATCH /api/projects/{id}`
- `DELETE /api/projects/{id}`
- `POST /api/projects/{id}/files`
- `GET /api/projects/{id}/files`
- `POST /api/projects/{id}/parse-jobs`
- `GET /api/jobs/{id}`
- `GET /api/jobs/{id}/events`
- `GET /api/jobs/{id}/events/stream`
- `GET /api/projects/{id}/versions`
- `GET /api/projects/{id}/issues`
- `GET /api/projects/{id}/proposals`
- `POST /api/proposals/{id}/accept`
- `POST /api/proposals/{id}/reject`
- `POST /api/proposals/{id}/stash`
- `POST /api/projects/{id}/exports`
- `GET /api/projects/{id}/exports`
- `GET /api/providers`
- `GET /api/provider-configs`
- `POST /api/provider-configs`
- `POST /api/provider-configs/{id}/verify`
- `DELETE /api/provider-configs/{id}`
- `GET /api/access-code/status`
- `POST /api/access-code/verify`
- `POST /api/source-guardian/search`
- `POST /api/source-guardian/confirm`

## 安全边界

- 未确认 Proposal 不改变当前导出版本
- Story2Paper 实验正文不会直接写入默认导出版本
- 参考文献只整理已有文本，不补造作者、刊名、卷期、DOI
- 未确认联网来源不影响 Compliance Auditor 结论
- API key 不返回前端；当前实现服务端封存密钥，前端只看到 `has_api_key`
- 自定义 Provider `base_url` 默认拦截内网、本机、link-local、保留和组播地址
- Link-local、reserved、multicast 地址始终拦截；Ollama 本地地址必须通过 `allow_local` 显式允许
- 设置 `SCNU_SECRET_KEY` 后使用部署密钥封存 Provider key；未设置时仅使用开发环境 insecure local key

## 当前限制

- 解析任务当前同步执行，Celery / Redis 仍是部署预留
- MinIO/S3 SDK 尚未替换本地文件系统 adapter
- PDF 只做本地粗解析；复杂版面需要人工复核
- 图片 OCR 是占位入口，需后续接本地或远程 OCR Provider
- PDF 导出当前保留 `.docx` 并记录转换降级
- 真实 LLM Provider 调用尚未接入 Agent Runtime
- Alembic 迁移脚本尚未建立；当前仅有幂等 schema bootstrap 补齐新增列

## 验收命令

```bash
uv run pytest tests -q
npm run test:smoke --prefix web
npm run build --prefix web
uv run python scripts/build_web_public.py
uv run python scripts/export_compliance_fixture.py tmp/fixture-export.docx
uv run python scripts/check_docx_compliance.py tmp/fixture-export.docx
```
