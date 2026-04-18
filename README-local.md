# SC-TH 本地运行说明

本文件只描述本地开发、验收与部署前检查。

当前主线固定为：

`快速导出：上传 .docx / 粘贴文本 → 统一结构识别 → 预检确认 → 规范驱动导出 .docx → 合规检查`

Workbench v1 本地骨架为：

`项目向导 → 隐私模式 → 上传材料 → 解析任务 → baseline version → Issue / Proposal → 用户确认 → 导出记录`

## 依赖

- Python 3.12
- Node.js 20+
- `uv`
- `npm`

安装依赖：

```bash
cd /Users/ethan/scnu-thesis-portal
uv sync --extra dev
npm install --prefix web
```

## 本地开发

启动后端：

```bash
uv run uvicorn backend.app.main:app --reload --port 8000
```

启动前端：

```bash
VITE_API_BASE_URL=http://127.0.0.1:8000 npm run dev --prefix web
```

默认访问：

- 前端：`http://127.0.0.1:5173`
- Workbench：`http://127.0.0.1:5173/#/workbench`
- 后端：`http://127.0.0.1:8000`

## 自托管依赖

Workbench 的完整部署形态预留以下服务：

- `web`
- `api`
- `worker`
- `postgres`
- `redis`
- `minio`

本地可用 Docker Compose 启动骨架：

```bash
docker compose up --build
```

当前默认开发模式仍可使用 SQLite + 本地文件系统，不要求先启动 Docker。

## 类型与构建

生成前端类型：

```bash
uv run python scripts/generate_frontend_types.py
```

构建前端并写入 `public/`：

```bash
uv run python scripts/build_web_public.py
```

## 本地验收

推荐至少走以下链路：

1. 上传合法 `.docx`
2. 粘贴合法文本
3. 检查预检弹窗是否显示“缺失章节保留留白位”和“复杂元素需人工复核”
4. 检查正式封面已作为主线输出的一部分
5. 通过预检后导出 `.docx`
6. 运行 `uv run python scripts/check_docx_compliance.py <导出文件>`
7. 在 Word 中更新目录并抽查页眉页脚、页码和分页
8. 进入 `#/workbench` 新建项目
9. 上传 `.docx` 或文本文件并触发解析
10. 检查版本、Agent 事件、Proposal 队列与导出历史
11. 检查 Provider 配置不会向前端返回 API key，内网 base URL 默认被拦截
12. 如需访问码保护，设置 `SCNU_ACCESS_CODE` 并确认未验证请求会返回 `ACCESS_CODE_REQUIRED`

CI 使用的导出合规 fixture 可本地生成：

```bash
uv run python scripts/export_compliance_fixture.py tmp/fixture-export.docx
uv run python scripts/check_docx_compliance.py tmp/fixture-export.docx
```

更细的人工验收项见 `docs/local-validation-word.md`。
