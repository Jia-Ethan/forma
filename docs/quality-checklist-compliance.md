# SC-TH 严格合规质量清单

本清单对应《华南师范大学本科生毕业论文（设计）手册》与《华南师范大学本科毕业论文（设计）撰写基本规范》当前采用口径的自动化与人工验收基线。

## 自动可验证项

- A4 纸张与纵向页面设置
- 上 2.5cm / 下 2.5cm / 左 2cm / 右 2cm
- 左侧装订线 0.5cm
- `ThesisTitle`、`ChineseAbstractHeading`、`ChineseAbstractBody`、`EnglishAbstractHeading`、`EnglishAbstractBody`、`KeywordsLabel`、`TOCHeading`、`Heading1`–`Heading4`、`BodyText`、`ReferenceHeading`、`ReferenceEntry`、`AppendixHeading`、`AppendixItemHeading`、`AcknowledgementHeading`、`NoteText`
- 正文 `BodyText` 为小四宋体、1.25 倍行距
- 外文摘要 `EnglishAbstractBody` 为 `Times New Roman`
- 目录字段存在且覆盖 `Heading1`–`Heading4`
- 页眉为论文题目
- 页脚存在连续阿拉伯页码字段
- 顺序符合当前口径：中文摘要 -> 外文摘要 -> 目录 -> 正文与注释 -> 参考文献 -> 附录 -> 致谢
- 文档前部未出现疑似学校正式封面文案

## 人工复核项

- 中文摘要是否真正落在 250–300 字最佳区间
- 外文摘要是否真正不超过 250 个实词
- 论文题目是否包含副题且页眉是否需要人工删减
- 参考文献条目是否完全符合 GB3469-83 细节
- 注释编号、页末注 / 篇末注是否符合规范
- 图题、表题位置与编号是否符合规范
- 数字、单位、标点、术语、外文字母的全文级规范化
- 复杂 `.docx` 中图片、表格、脚注、浮动对象是否发生迁移失真

## 已知限制项

- 不自动生成学校统一正式封面
- 不自动保证注释为校规级页末注 / 篇末注
- 不自动保证图题 / 表题全量重建
- 不自动保证复杂富文本对象高保真迁移
- 不自动修正全部参考文献格式细项

## 本轮结论

- 自动可验证的硬性页面与样式项：已落地
- 复杂内容、注释、图表题注、参考文献细项：仍需人工复核
- 当前结论：**主体已达标，但存在若干需人工复核项**
