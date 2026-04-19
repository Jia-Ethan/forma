# Workbench vNext

Workbench vNext 的目标不是把论文工具包装成聊天机器人，而是把论文材料、审查、建议、版本和导出组织成可追溯的项目空间。

## 默认项目配置

```text
school = scnu
degree_level = undergraduate
template_profile = scnu-undergraduate
privacy_mode = local_only
remote_provider_allowed = false
```

## Project Workspace

必须支持：

- 项目创建向导
- 项目设置
- 文件库
- 当前版本
- 版本历史
- 导出历史
- Proposal Queue
- Audit Log
- 隐私模式
- Provider 授权状态

## Thesis Pipeline

```text
Upload Materials
→ Parse Sources
→ Build NormalizedThesis
→ Generate Issue Map
→ Generate Draft / Proposal
→ User Approval
→ New Version
→ Export / Package
```

## Agent Roles

- Director Agent: 决定下一步调用哪个 Agent
- Intake Parser: 解析上传材料
- Thesis Structurer: 建立论文结构树
- Compliance Auditor: 检查格式、章节、页码、参考文献、复杂元素
- Writing Collaborator: 基于用户材料生成草稿候选
- Comment Resolver: 处理老师批注并生成修订 Proposal
- Reference Curator: 整理参考文献，不补造元数据
- Integrity Guard: 标记无来源事实、伪造风险、学术诚信风险
- Export Agent: 生成 `.docx`、Markdown、自检报告、PDF、项目包

## Proposal Rule

所有 AI 或规则候选内容必须进入 Draft / Proposal。未确认 Proposal 不影响当前版本。

接受 Proposal 后：

1. 记录 approval
2. 生成新 version
3. 写入 audit log
4. 保留 source refs 和风险说明

## Demo Project

公开站的 Workbench demo project 只展示信息结构：

- 示例文件库
- 示例 Issue Map
- 示例 Proposal Queue
- 示例版本历史
- 示例导出历史
- 本地优先状态

它不包含真实论文正文，不调用远程 Provider，也不保存用户数据。

v0.4 public demo 支持前端本地交互：

- 点击 Proposal 改变 accepted / stashed / rejected 状态
- 切换 baseline 与 accepted 版本
- 触发模拟导出历史
- 一键重置 demo
- 禁止上传真实论文
