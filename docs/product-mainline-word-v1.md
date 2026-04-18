# SC-TH 主线说明

当前产品保留两条入口：

- 快速入口：`规范驱动的章节映射 + Word 模板渲染`
- Workbench v1：`项目向导 + 隐私模式 + 文件库 + 版本 + 建议队列 + 可追溯导出`

它不再把导出结果定义为“正文审查稿”，而是把 `.docx` 结果作为华南师范大学本科毕业论文送审稿基线。智能辅助只生成候选建议；未确认内容不得改变当前导出版本。

## 产品目标

- 输入 `.docx` 或粘贴文本
- 统一识别为标准化论文结构
- 按学校规范生成稳定 `.docx`
- 让正式封面、前后置顺序、目录字段、页眉页脚、页码、分页与关键样式可控
- 在 Workbench 中保留项目文件、版本、导出历史、Issue 和 Proposal 记录
- 确保正文相关改动只能通过用户确认后的 Proposal 写入新版本

## 当前主路径

1. 首页接受 `.docx` 上传或纯文本输入
2. 后端统一抽取为中间结构 `NormalizedThesis`
3. 预检弹窗展示阻塞项 / 警告项 / 信息项
4. 通过预检后进入导出
5. 下载 `.docx`
6. 运行合规脚本并做必要人工复核

## Workbench 路径

1. 打开 `#/workbench`
2. 通过项目向导创建论文项目并选择写作阶段、隐私模式
3. 上传 `.docx`、PDF、文本、图片/OCR 占位或参考文献文件
4. 后端保存 `ProjectFile` 并写入本地对象存储
5. parser registry 解析材料并生成 `NormalizedThesis v2`
6. 系统创建 baseline version、Issue Ledger、规则 Proposal 和 Agent events
7. 用户逐条接受 / 拒绝 / 暂存 Proposal
8. 接受影响导出的 Proposal 时创建新版本
9. 通过 export registry 生成 `.docx`、Markdown、自检报告或 PDF 降级记录

## 规范优先级

当前实现固定按以下顺序仲裁：

`2025 学校规范 PDF > 学生手册 .doc（补充项）> main.pdf > 旧模板 / README / 旧逻辑`

## 当前固定规则

- 正式封面纳入主线第一页
- 缺失字段与缺失章节一律留白，不虚构内容
- 目录使用 Word 字段，不导出静态目录文本
- 前置部分用大写罗马页码，正文从阿拉伯页码 `1` 开始
- 页眉统一使用主标题，超长按固定字符规则截断，不换行
- 表格、图片、脚注、文本框、形状等复杂元素进入人工复核

## 页面级结果

1. 正式封面
2. 中文摘要
3. 英文摘要
4. 目录
5. 正文
6. 参考文献
7. 附录
8. 致谢

如输入存在显式“注释”章节，则放在正文后、参考文献前。

## 当前 Workbench 骨架

- 数据层：SQLAlchemy 模型覆盖项目、文件、来源、版本、blocks、issues、proposals、approvals、agent runs/events、exports、provider configs、audit logs
- 存储层：默认 SQLite + 本地文件系统，Docker Compose 预留 Postgres、Redis、MinIO
- 安全层：Provider key 不返回前端；访问码可保护私有部署；自定义 base URL 默认拦截内网、本机和 link-local 地址；Ollama 需显式允许本地访问
- 事件层：支持 REST 事件列表和 SSE 事件流端点
- UI 层：三栏 Workbench 壳，覆盖项目向导、项目设置、Provider 设置、隐私提示、文件区、文档预览、版本历史、Agent 面板、建议队列和导出历史
