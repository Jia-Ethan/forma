# SC-TH 质量清单 v2

本清单保留作为轻量入口，但内容已同步到新主线。

## 入口与预检

- 首页维持极简输入壳层，不额外扩展主视觉
- 预检弹窗一次性展示阻塞项 / 警告项 / 信息项
- 缺失章节说明为“保留留白位”，不再使用“必须补足后才能继续”的旧口径

## 导出结果

- 产物为规范化 `.docx`
- 正式封面进入主线第一页
- 目录为 Word 字段
- 页眉页脚、页码与分节规则稳定

## 自动检查

- `uv run pytest tests -q`
- `npm run test:smoke --prefix web`
- `npm run build --prefix web`
- `python3 scripts/build_web_public.py`
- `python3 scripts/check_docx_compliance.py <docx-path>`
