# 本地 MVP 验证

> 历史阶段记录：本文档保留旧本地 job 模式的验证结果，不再代表当前线上主路径。当前主线见 `docs/architecture-mainline-v1.md`。

本文件用于记录本轮本地 MVP 的实际验收结果。

## Case 1：结构化粘贴输入

- 状态：已验证
- 输入：
  - 接口：`POST /api/jobs/from-form`
  - 数据源：`examples/input/structured-input-example.json`
- 预期：
  - 成功创建任务
  - 成功生成 PDF 和 `.tex` 工程 zip
- 实际：
  - 真实任务 ID：`21bf87e66309`
  - 状态：`completed`
  - 产物：
    - `outputs/jobs/21bf87e66309/thesis.pdf`
    - `outputs/jobs/21bf87e66309/tex-project.zip`
    - `outputs/jobs/21bf87e66309/compile.log`
- 结果：通过

## Case 2：上传规范 `.docx`

- 状态：已验证
- 输入：
  - 接口：`POST /api/jobs/from-docx`
  - 文件：`tests/fixtures/sample-thesis.docx`
- 预期：
  - 能抽取摘要、Abstract、正文、参考文献、致谢、附录
  - 成功生成 PDF 和 `.tex` 工程 zip
- 实际：
  - 真实任务 ID：`2163d49b2d80`
  - 状态：`completed`
  - 系统识别出：
    - `abstract_cn`
    - `abstract_en`
    - `body`
    - `references`
    - `acknowledgements`
    - `appendix`
  - 产物：
    - `outputs/jobs/2163d49b2d80/thesis.pdf`
    - `outputs/jobs/2163d49b2d80/tex-project.zip`
    - `outputs/jobs/2163d49b2d80/compile.log`
- 结果：通过

## Case 3：故意制造异常

- 状态：已验证
- 输入：
  - 以环境变量 `SCNU_EXTRA_REQUIRED_STYLES=missing-style-for-validation.sty` 启动后端
  - 对 `POST /api/jobs/from-form` 提交结构化输入
- 预期：
  - 后端在预检阶段识别缺失依赖
  - 任务失败，但返回明确错误，不崩溃
- 实际：
  - `/api/health` 返回缺失样式 `missing-style-for-validation.sty`
  - 真实任务 ID：`298f0d801358`
  - 状态：`failed`
  - 错误码：`TEX_ENV_MISSING`
  - 错误消息：`本地 TeX 环境不完整，无法开始编译。`
- 结果：通过

## 剩余问题

- 当前真实成功依赖用户级 TeX 宏包安装，至少需要补齐 `titlesec` 包。
- `.docx` 输入对“封面标题与正文首段混在一起”的情况仍会给出一条 warning，但不会阻塞生成。
- 当前前端交互已可本地访问，但未做浏览器自动化 UI 回归。
