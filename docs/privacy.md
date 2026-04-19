# Privacy Boundary

SCNU Thesis Agent Workbench 的默认策略是 local-first。

公开站用于体验产品主线，不适合作为真实论文长期项目空间。真实论文、Provider key、远程模型授权和长期版本管理建议放在私有部署。

## 公开站默认行为

- 不启用远程 LLM Provider
- 不向 AI 发送真实论文正文
- 允许快速 `.docx` 预检与规范化导出
- 允许查看静态 Workbench demo project
- 不向匿名用户开放 Provider 设置入口
- 上传文件处理完成后删除，导出文件只保留 30 分钟
- 匿名入口需要隐私确认、Turnstile 校验与 IP 限流
- 日志只记录时间、IP hash、文件大小、耗时、状态码和错误码，不记录正文内容

## Provider 边界

前端可见：

- provider id
- display name
- models
- capabilities
- remote / local
- configured
- verified

前端不可见：

- api key
- secret
- full raw config
- 论文正文

远程 Provider 必须满足：

- 项目级授权
- 可撤销
- 输出进入 Draft / Proposal
- 用户确认后才生成新版本

## Academic Integrity

项目不做：

- 代写定位
- 查重率承诺
- 数据、实验、问卷、参考文献伪造
- 无来源事实补全
- 研究生论文模板
- 多学校公开入口

AI 只应帮助整理、审查、解释、生成候选修订。候选内容必须由用户确认其事实来源与学术诚信风险。
