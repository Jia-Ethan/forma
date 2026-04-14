# SC-TH 严格合规质量清单

本清单对应《华南师范大学本科生毕业论文（设计）手册》与《华南师范大学本科毕业论文（设计）撰写基本规范》当前采用口径的自动化与人工验收基线。

## 自动可验证项

- A4 纸张与纵向页面设置
- 上 2.5cm / 下 2.5cm / 左 2cm / 右 2cm
- 左侧装订线 0.5cm
- `ThesisTitle`、`ChineseAbstractHeading`、`ChineseAbstractBody`、`EnglishAbstractHeading`、`EnglishAbstractBody`、`KeywordsLabel`、`TOCHeading`、`Heading1`–`Heading4`、`BodyText`、`ReferenceHeading`、`ReferenceEntry`、`AppendixHeading`、`AppendixItemHeading`、`AcknowledgementHeading`、`NoteText`
- 正文 `BodyText` 为小四宋体、1.25 倍行距
- 英文摘要页标题为 `Abstract`
- 英文摘要 `EnglishAbstractBody` 为 `Times New Roman`
- 目录字段存在且覆盖 `Heading1`–`Heading4`
- 页眉为剥离常见副标题后的论文主标题
- 页脚存在连续阿拉伯页码字段
- 顺序符合当前口径：中文摘要 -> `Abstract` -> 目录 -> 正文与注释 -> 参考文献 -> 附录 -> 致谢
- 首个正文标题即使从二级 / 三级 / 四级起步，也不会生成 `0.*` 前导零编号
- 英文关键词前缀兼容 `Keyword:`、`Keywords:`、`Key words:`
- `参考文献`、`注释`、`附录` 区块中的编号条目不会被正文标题识别规则直接掏空
- 文档前部未出现疑似学校正式封面文案
- 三份 `examples/compliance` 样例已接入 `parse -> precheck -> export -> compliance` 自动化链路

## 人工复核项

- 中文摘要是否真正落在 250–300 字最佳区间
- 英文摘要是否真正不超过 250 个实词
- 极少数歧义性主副标题写法是否仍需人工调整页眉
- 极少数歧义性数字编号短句是否需要人工判定为标题或列表项
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
- `Abstract` 页标题、页眉主标题剥离、编号标题收紧、关键词前缀兼容、样例全链路与 CI：已落地
- 复杂内容、注释、图表题注、参考文献细项：仍需人工复核
- 当前结论：**主体已达标，但存在若干需人工复核项**
