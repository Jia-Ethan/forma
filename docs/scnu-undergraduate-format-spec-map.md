# 华南师范大学本科论文导出规范映射表

本表是当前导出逻辑、测试、合规检查与人工验收的统一依据。

固定仲裁规则：

`2025 学校规范 PDF > 学生手册 .doc（仅补充未写明项）> templates/upstream/latex-scnu/main.pdf > 旧模板 / README / 旧逻辑`

## main.pdf 页角色基线

- `p1`：正式封面
- `p2`：中文摘要
- `p3`：英文摘要
- `p4-p5`：目录
- `p6+`：正文
- 正文后：参考文献 / 附录 / 致谢

冲突说明：

- `main.pdf` 中“附录先于参考文献”的顺序不作为当前主线依据。
- 当前主线按学校规范固定输出：参考文献 → 附录 → 致谢。

## 映射主表

| source_basis | input_source | normalized_field | render_slot | page_role | numbering | style_rule | conflict_note |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2025 规范 PDF + main.pdf p1 | `.docx` / 文本封面字段 | `cover.title` | `cover.title_block` + `cover.title_field` | 正式封面 | 不编页码 | 黑体大标题，缺失留白 | `main.pdf` 标题样式作视觉基线 |
| 2025 规范 PDF + 学生手册 | `.docx` / 文本封面字段 | `cover.advisor` | `cover.field.advisor` | 正式封面 | 不编页码 | 小四号宋体，值槽位留白 | 学生手册补充字段与页码规则 |
| 2025 规范 PDF + 学生手册 | `.docx` / 文本封面字段 | `cover.student_name` | `cover.field.student_name` | 正式封面 | 不编页码 | 小四号宋体，值槽位留白 | 无冲突 |
| 2025 规范 PDF + 学生手册 | `.docx` / 文本封面字段 | `cover.student_id` | `cover.field.student_id` | 正式封面 | 不编页码 | 小四号宋体，值槽位留白 | 无冲突 |
| 2025 规范 PDF + 学生手册 | `.docx` / 文本封面字段 | `cover.school` | `cover.school_mark` | 正式封面 | 不编页码 | 学校名固定为华南师范大学 | 默认值来自实现锁定 |
| 2025 规范 PDF + 学生手册 | `.docx` / 文本封面字段 | `cover.department` | `cover.field.department` | 正式封面 | 不编页码 | 小四号宋体，值槽位留白 | 无冲突 |
| 2025 规范 PDF + 学生手册 | `.docx` / 文本封面字段 | `cover.major` | `cover.field.major` | 正式封面 | 不编页码 | 小四号宋体，值槽位留白 | 无冲突 |
| 2025 规范 PDF + 学生手册 | `.docx` / 文本封面字段 | `cover.class_name` | `cover.field.class_name` | 正式封面 | 不编页码 | 小四号宋体，值槽位留白 | 无冲突 |
| 2025 规范 PDF + 学生手册 | `.docx` / 文本封面字段 | `cover.graduation_time` | `cover.field.graduation_time` | 正式封面 | 不编页码 | 小四号宋体，值槽位留白 | 学生手册字段名更细 |
| 2025 规范 PDF + main.pdf p2 | `.docx` / 文本摘要段落 | `abstract_cn.content` | `front.abstract_cn.content` | 中文摘要 | 前置罗马页码 | 标题小二号黑体加粗，正文小四号宋体 | `main.pdf` 标题文案为“摘要”，当前沿用 |
| 2025 规范 PDF | `.docx` / 文本关键词 | `abstract_cn.keywords[]` | `front.abstract_cn.keywords` | 中文摘要 | 前置罗马页码 | “关键词”标签 + 小四号宋体 | 缺失留白 |
| 2025 规范 PDF + main.pdf p3 | `.docx` / 文本英文摘要段落 | `abstract_en.content` | `front.abstract_en.content` | 英文摘要 | 前置罗马页码 | 标题 `Abstract`，正文小四号 Times New Roman | 以手册“英文单词标题”补充 |
| 2025 规范 PDF | `.docx` / 文本英文关键词 | `abstract_en.keywords[]` | `front.abstract_en.keywords` | 英文摘要 | 前置罗马页码 | `Keywords` 标签 + Times New Roman | 缺失留白 |
| 2025 规范 PDF + main.pdf p4-p5 | 固定生成 | `toc` | `front.toc.field` | 目录 | 前置罗马页码 | 标题小二号黑体加粗，目录项小四号宋体 1.25 倍行距 | 目录本身固定纳入 TOC |
| 2025 规范 PDF + 学生手册 | `.docx` / 文本正文标题 | `body_sections[].title` | `body.heading[level]` | 正文 | 阿拉伯页码从 1 开始 | 一级居中；二至四级顶格；统一编号体例 | 正文内容尽量保留原文 |
| 2025 规范 PDF + 学生手册 | `.docx` / 文本正文段落 | `body_sections[].content` | `body.paragraphs` | 正文 | 阿拉伯页码连续 | 小四号宋体，1.25 倍行距，首行缩进 | 不做语义重写 |
| 学生手册补充 | 显式“注释”标题或注释段落 | `notes` | `body.notes` | 注释 | 阿拉伯页码连续 | 小五/小四号近似正文，人工复核 | 仅显式章节会渲染；脚注默认人工复核 |
| 2025 规范 PDF + main.pdf 末段 | `.docx` / 文本参考文献段落 | `references[]` | `back.references` | 参考文献 | 阿拉伯页码连续 | 标题小二号黑体；条目悬挂缩进，小四号宋体 | 顺序按学校规范固定在附录前 |
| 2025 规范 PDF | `.docx` / 文本附录标题与段落 | `appendices[]` | `back.appendices` | 附录 | 阿拉伯页码连续 | 顶层“附录”标题 + 附录子标题 | 缺失保留附录章节空白区 |
| 2025 规范 PDF + main.pdf 末页 | `.docx` / 文本致谢段落 | `acknowledgements` | `back.acknowledgements` | 致谢 | 阿拉伯页码连续 | 标题小二号黑体；正文小四号宋体 | 缺失保留致谢章节空白区 |
| 学生手册 | 固定渲染 | `cover.title` | `header.text` | 页眉 | 前置/正文统一 | 五号宋体，主标题单行居中，不换行 | 超长按固定字符权重截断 |
| 学生手册 + 实现约束 | 固定渲染 | `PAGE field` | `footer.page_number` | 页脚页码 | 前置罗马 / 正文阿拉伯 | 五号黑体加粗，居中 | 封面节关闭页码 |

## 复杂元素策略

| source_basis | input_source | normalized_field | render_slot | page_role | numbering | style_rule | conflict_note |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 当前主线实现 | `.docx` 中表格 / 图片 / 脚注 / 文本框 / 形状 / 域代码 | `source_features` + `manual_review_flags` | `precheck.complex_elements` | 预检提示 | 不适用 | 只提示，不强行高保真重排 | 标记 `MANUAL_REVIEW`，不作为默认阻塞项 |
