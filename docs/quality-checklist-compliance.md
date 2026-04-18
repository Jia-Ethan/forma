# SC-TH 合规清单

本清单对应当前“华南师范大学本科论文导出结果合规”主线。

## 主线口径

- README 与文档不再保留“正文审查稿”“不生成学校正式封面”旧口径
- 规则仲裁已固定写入文档
- `main.pdf` 作为页角色与展示样式基线，而不是顺序唯一来源

## 输入链路

- `.docx` 上传与粘贴文本共用同一套 `NormalizedThesis`
- 任一入口都不会绕过中间结构直接写段落
- 复杂元素会进入 `manual_review_flags`

## 导出结果

- 正式封面为第一页
- 中文摘要、英文摘要、目录、正文、参考文献、附录、致谢顺序正确
- 缺失章节保留留白位，不写“待补充”“未填写”“请自行填写”
- 目录为 Word 字段
- 前置部分大写罗马页码，正文阿拉伯页码从 `1` 开始
- 页眉为主标题单行居中
- 页脚页码居中
- 关键样式显式写入

## 自动检查

- `uv run pytest tests -q`
- `npm run test:smoke --prefix web`
- `npm run build --prefix web`
- `uv run python scripts/build_web_public.py`
- `uv run python scripts/export_compliance_fixture.py tmp/fixture-export.docx`
- `uv run python scripts/check_docx_compliance.py tmp/fixture-export.docx`

## 人工复核

- 在 Word 中更新目录字段
- 抽查正式封面字段留白位
- 抽查页眉截断、页码、分页与节切换
- 抽查表格、图片、脚注、文本框等复杂元素
