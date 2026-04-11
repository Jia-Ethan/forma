# scnu-thesis-portal

面向华南师范大学论文写作场景的结构识别与模板导出 web-app。

## 当前线上可用能力

- 上传 `.docx`
- 粘贴正文文本
- 识别摘要、Abstract、正文章节、参考文献、致谢、附录
- 在网页内补全和修正字段
- 导出规范化 `.tex` 工程 zip

## 当前明确边界

- 仅支持 `.docx`，不支持 `.doc`
- 不保留原 Word 样式
- 复杂表格、图片、脚注、特殊排版未完整支持
- 当前不是学校官方认证工具
- 当前不承诺学校模板已逐条核验完成
- 生产环境默认不承诺 PDF 导出

## 项目结构

- `web/`：React + Vite 前端
- `backend/`：Python 业务逻辑与 API
- `index.py`：Vercel FastAPI 入口
- `templates/working/latex-scnu-web/`：当前首轮主线工作模板
- `templates/upstream/`：保留的上游参考模板
- `docs/`：审查、范围、部署、验收文档
- `examples/`：示例输入材料

## 本地开发

```bash
cd /Users/ethan/scnu-thesis-portal
uv sync --extra dev
npm install --prefix web
uv run uvicorn backend.app.main:app --reload --port 8000
```

另开一个终端：

```bash
cd /Users/ethan/scnu-thesis-portal
npm run dev --prefix web
```

## Vercel 部署

部署说明见：

- `docs/deploy-vercel.md`

预览地址：

- 待本轮预览部署完成后补充

## Roadmap

- `v0.2`：首轮上线为结构识别、字段修正、`.tex` zip 导出
- `v0.3`：继续完善复杂 `.docx` 识别、体验与错误反馈
- `v0.4+`：在验证环境稳定后，再评估是否恢复线上 PDF
