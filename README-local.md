# SC-TH 本地运行说明

本文件只描述本地开发与本地验收方式。当前产品主线是：

`上传 .docx / 粘贴文本 → 预检确认弹窗 → 海浪导出进度 → 自动下载 .docx`

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

## 本地构建

生成前端类型：

```bash
python3 scripts/generate_frontend_types.py
```

构建前端并写入 `public/`：

```bash
python3 scripts/build_web_public.py
```

## 本地验证

推荐至少走这几步：

1. 上传合法 `.docx`
2. 粘贴足量文本
3. 查看预检确认弹窗
4. 验证阻塞项禁用确认按钮
5. 取消返回首页并保留输入
6. 通过预检后进入海浪进度
7. 自动下载 `.docx`
8. 验证非法格式、空输入、模板缺失等错误提示

详细验收项见 `docs/local-validation-word.md`。
