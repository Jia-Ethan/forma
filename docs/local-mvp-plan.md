# 本地 MVP 方案

> 历史阶段记录：本文档保留本地 demo 方案，不再代表当前产品主路径。当前主线见 `docs/architecture-mainline-v1.md`。

## 1. 架构图（文字版）

前端 `web/`：

- React + TypeScript + Vite
- 展示两种输入方式
- 收集封面字段和内容字段
- 提交任务
- 轮询任务状态
- 展示成功 / 失败信息
- 下载 PDF 和 `.tex` 工程 zip

后端 `backend/`：

- FastAPI
- 校验输入
- 解析 `.docx`
- 标准化为章节结构
- 复制工作模板
- 生成 `.tex` 文件
- 调用 XeLaTeX 编译
- 导出 PDF 和 zip
- 记录日志和 manifest

文件系统：

- `templates/working/latex-scnu-web/`：工作模板基线
- `tmp/jobs/{job_id}/`：任务临时目录
- `outputs/jobs/{job_id}/`：最终产物和日志

## 2. 输入输出 contract

### 输入方式 A：结构化表单

封面与元信息：

- `title`
- `author_name`
- `student_id`
- `department`
- `major`
- `class_name`
- `advisor_name`
- `submission_date`

内容字段：

- `abstract_cn`
- `abstract_en`
- `keywords_cn`
- `keywords_en`
- `body`
- `references`
- `acknowledgements`
- `appendix`

### 输入方式 B：上传 `.docx`

- 仅支持 `.docx`
- 同时要求提交封面元信息
- 后端从文档中抽取：
  - 标题层级
  - 摘要 / Abstract
  - 正文段落
  - 参考文献 / 致谢 / 附录（如存在）

### 输出

- `job_id`
- 任务状态与错误信息
- 解析后的章节摘要
- 生成成功时：
  - PDF 下载链接
  - `.tex` 工程 zip 下载链接
  - 日志与 manifest 信息

## 3. docx 解析方案

- 使用 `python-docx`
- 按段落读取文本与样式
- 标题识别优先级：
  1. Word Heading 样式
  2. Markdown 标题写法
  3. 中文章节关键词（摘要、Abstract、参考文献、致谢、附录、第一章等）
- 抽取失败但正文存在时，退化为单章节正文
- 仅做结构提取，不尝试保留原 Word 样式

## 4. 模板映射方案

主线模板：`templates/working/latex-scnu-web`

每次生成时：

1. 复制模板到任务临时目录
2. 覆写以下文件：
   - `cover/image.tex`
   - `abstract/abstract-zh-CN.tex`
   - `abstract/abstract-en.tex`
   - `body/index.tex`
   - `reference/index.tex`
   - `thanks/index.tex`
   - `appendix/index.tex`
3. 根据章节内容按需生成正文 `.tex` 文件

正文映射规则：

- 结构化输入中的 `body` 支持 Markdown 风格标题
- `.docx` 解析出的章节保留为 section/subsection 层级
- 无章节时自动生成“正文”主章节

## 5. 编译方案

- 预检：
  - `xelatex`
  - `kpsewhich`
  - 关键 sty 宏包可用性
- 编译命令：
  - `xelatex -interaction=nonstopmode main.tex`
- 成功后打包整个工作目录为 zip
- 最终产物放到 `outputs/jobs/{job_id}/`

本轮不依赖 `latexmk`。

## 6. 错误处理策略

统一错误码：

- `TEX_ENV_MISSING`
- `DOCX_INVALID`
- `CONTENT_EMPTY`
- `FIELD_MISSING`
- `SECTION_PARSE_FAILED`
- `COMPILE_FAILED`
- `ARTIFACT_WRITE_FAILED`

策略：

- 后端返回结构化 JSON
- 前端把错误码和可读说明展示给用户
- 编译失败时保留 `compile.log`
- 即使失败，也尽量保留解析摘要与 manifest 方便排查

## 7. 本地运行依赖

Python：

- FastAPI
- Uvicorn
- python-docx
- pydantic
- Jinja2
- pytest
- httpx

Node：

- React
- React DOM
- React Router DOM
- Vite
- TypeScript

系统命令：

- `xelatex`
- `kpsewhich`
- `zip`

## 8. 验收标准

本地 MVP 完成后应满足：

- 首页可见两种输入方式
- 结构化输入能导出 PDF 和 `.tex` 工程 zip
- `.docx` 上传能成功走完整链路
- 错误场景能给出明确提示
- `outputs/` 中能看到 PDF、zip、log、manifest
- `tmp/` 中的工作目录不污染上游模板
