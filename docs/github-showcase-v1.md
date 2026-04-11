# GitHub Showcase v1

## About 区配置

建议并已应用：

- Description: `SCNU thesis web app: parse .docx/text, review fields, export a LaTeX project zip.`
- Website: `https://scnu-thesis-portal-git-feat-vercel-l-e3191b-jia-ethans-projects.vercel.app`
- Topics:
  - `scnu`
  - `thesis-template`
  - `latex`
  - `tex`
  - `docx`
  - `fastapi`
  - `react`
  - `vite`
  - `vercel`
  - `education-tools`

## 展示素材

当前已补：

- `docs/assets/vercel-launch-home.png`：首页截图。
- `docs/assets/vercel-launch-review.png`：解析结果与 review 页面截图。
- README 中补充 Mermaid 流程图：上传 / 粘贴 -> 解析 -> review / 修正 -> 导出 `.tex` 工程 zip。

## Release 判断

本阶段不建议立即发布首个 release。

原因：

- 当前主线仍在 PR #1 中，尚未合并到 `main`。
- README、质量清单和展示素材刚完成，需要先让 PR 合并后形成稳定基线。
- 线上 PDF 明确关闭，当前更适合标记为 preview MVP，而不是正式版本发布。

建议在 PR #1 合并后，如果线上预览和 README 均稳定，再创建 `v0.2.0-preview` 或 `v0.2.0` release，并在 release notes 中明确“不支持 `.doc`、不保留 Word 样式、线上 PDF 默认关闭”。
