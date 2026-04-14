# SC-TH 本地运行说明

本文件只描述本地开发、验收与部署前检查。

当前主线固定为：

`上传 .docx / 粘贴文本 → 统一结构识别 → 预检确认 → 规范驱动导出 .docx → 合规检查`

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
npm run dev --prefix web
```

默认访问：

- 前端：`http://127.0.0.1:5173`
- 后端：`http://127.0.0.1:8000`

## 类型与构建

生成前端类型：

```bash
python3 scripts/generate_frontend_types.py
```

构建前端并写入 `public/`：

```bash
python3 scripts/build_web_public.py
```

## 本地验收

推荐至少走以下链路：

1. 上传合法 `.docx`
2. 粘贴合法文本
3. 检查预检弹窗是否显示“缺失章节保留留白位”和“复杂元素需人工复核”
4. 检查正式封面已作为主线输出的一部分
5. 通过预检后导出 `.docx`
6. 运行 `python3 scripts/check_docx_compliance.py <导出文件>`
7. 在 Word 中更新目录并抽查页眉页脚、页码和分页

更细的人工验收项见 `docs/local-validation-word.md`。
