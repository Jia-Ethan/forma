# Vercel Launch Audit

## 1. 仓库现状总览

### 根目录

- `README.md`：仍然是资料仓库定位，不反映现有本地 MVP 或线上能力边界。
- `README-local.md`：描述的是本地双进程运行和本地 XeLaTeX 依赖，尚未区分线上与本地。
- `backend/`：已有 FastAPI 本地 MVP，核心能力包括 `.docx` 解析、结构映射、生成工作模板、编译 PDF。
- `web/`：已有 React + Vite 前端，但主流程是“提交后跳转 job 详情页轮询状态”。
- `docs/`：已有本地 MVP 审查、方案、验证文档，但没有 Vercel 上线边界文档。
- `tests/`：已有基础 pytest，覆盖 `.docx` 解析和旧 job API。
- `examples/`：已有示例输入与输出说明。
- `scripts/`：目前基本为空，缺少前端构建、类型生成、部署辅助脚本。
- `templates/working/latex-scnu-web/`：已从 upstream 复制出的工作模板，是当前唯一真正接入自动生成链路的模板。
- `templates/upstream/`：保留三套上游模板，当前主要用于参考与后续扩展，不应进入首轮线上主链路。
- `outputs/`、`tmp/`：本地 job 工件与调试目录，本地 MVP 运行依赖它们作为状态来源。

### backend/

- `backend/app/main.py`
  - 当前提供 `GET /api/health`
  - 当前提供 `/api/jobs/from-form`、`/api/jobs/from-docx`
  - 当前提供 `/api/jobs/{job_id}` 与产物下载接口
  - 使用线程异步处理 job，并把前端页面构建产物挂在 FastAPI 下
- `backend/app/parser.py`
  - 能解析 `.docx` 段落
  - 能按 Heading 样式、Markdown 标题、中文章节名识别结构
  - 当前重点是段落和标题识别，不支持复杂 Word 样式保留
- `backend/app/generator.py`
  - 同时负责 job 生命周期、模板写入、XeLaTeX 编译、zip 导出、manifest 更新
  - 当前是本地 demo 的关键耦合点
- `backend/app/schemas.py`
  - 有请求与 job 状态 schema
  - 没有面向线上首轮的 normalized thesis schema
- `backend/pyproject.toml`
  - 当前只服务本地后端，不利于 Vercel 在仓库根识别 Python 入口

### web/

- `web/src/App.tsx`
  - 首页支持两种输入：上传 `.docx`、结构化表单
  - 提交后跳转 `/jobs/:jobId` 轮询状态
  - UI 更接近开发演示，不是普通学生可直接使用的同步向导流程
- `web/src/types.ts`
  - 当前手写维护前端类型
  - 与后端 schema 没有统一来源
- `web/src/styles.css`
  - 样式可用，但没有面向正式产品首轮上线的信息结构
- `web/package.json`
  - 仅含基本 Vite 构建
  - 当前没有 smoke test 依赖

### docs/

- 现有文档集中在“本地 MVP 是否可跑通”
- 缺少：
  - 面向线上能力边界的审查
  - 面向首轮上线的产品范围判断
  - Vercel 部署说明
  - 线上/本地统一验收清单

### tests/

- 当前 pytest 覆盖：
  - 健康检查
  - 非 `.docx` 拒绝
  - 合法 `.docx` job 创建
  - `.docx` 解析
  - Markdown 转正文
- 当前不覆盖：
  - 同步解析接口
  - 线上主路径 `.tex` zip 导出
  - 生产环境 PDF 关闭
  - 前端主流程 smoke test

### examples/

- 有规范 `.docx` 和结构化输入示例
- 可以继续作为首轮线上 demo 的手工验收材料

### scripts/

- 当前为空
- 首轮上线缺少：
  - 前端构建产物同步到 `public/` 的脚本
  - 前后端共享类型生成脚本
  - 部署辅助脚本

### templates/working/

- 当前主线模板是 `templates/working/latex-scnu-web/`
- 已适配封面、摘要、正文、参考文献、致谢、附录自动覆盖
- 仍残留大量样例论文材料、样例 PDF、示例代码和正文文件
- 如果直接纳入线上打包，会增大函数包体积，也会增加维护噪音

### templates/upstream/

- `latex-scnu`：当前 working 模板来源，适合作为本科首轮主线参考
- `scnuthesis-scnu`：仍适合作为后续对照和研究生/更完整模板参考
- `scnuthesis-zsben2`：更偏研究生场景与现代化实现参考
- 首轮上线不应把任何 upstream 模板对外宣传为“官方核验完成”

## 2. 当前代码已实现能力

- 读取 `.docx` 文件并提取段落文本
- 识别部分标题层级与常见章节
- 将提取结果映射到当前本科工作模板
- 生成 `.tex` 工程
- 在本地 XeLaTeX 环境下生成 PDF
- 同时导出 `.tex` 工程 zip
- 前端可提交 `.docx` 或结构化内容
- 有基础错误返回，如文件为空、文件类型错误、TeX 依赖缺失、编译失败

## 3. 当前未实现能力

- 面向普通用户的同步向导式编辑体验
- 统一 normalized thesis schema
- 前后端共享类型生成
- 面向线上环境的同步 API 设计
- 生产环境与本地环境的 capability flags
- Vercel 部署配置
- 生产环境稳定可用的 PDF 能力
- 复杂 `.docx` 内容支持，例如表格、图片、脚注、复杂列表、内嵌公式
- 官方格式核验

## 4. 仅限本地的能力

- 依赖本机 XeLaTeX / kpsewhich / TeX Live 宏包
- 依赖 `outputs/jobs`、`tmp/jobs` 存放工件与任务状态
- 依赖后台线程和 job polling
- 依赖 FastAPI 托管前端构建产物
- 本地 PDF 编译与日志落盘

这些能力本质上是“本地 demo 运行方式”，不是首轮线上主架构。

## 5. 适合首轮上线的能力

- 上传 `.docx` 后解析为结构化内容
- 粘贴文本后做章节识别和标准化
- 在网页内补全 metadata、摘要、Abstract、正文章节、参考文献、致谢、附录
- 将修正后的 normalized thesis 导出为规范化 `.tex` 工程 zip
- 在页面明确提示当前支持范围、已知限制、非官方性质

## 6. 首轮绝对不能对外承诺的能力

- 在线完整替代论文排版流程
- 学校官方模板已逐条核验完成
- 任意 `.docx` 一键修复为合规论文
- 保留原 Word 样式、分页、图片布局、表格样式
- 复杂参考文献自动修复
- 本科/硕士/博士全模板统一支持
- 生产环境稳定 PDF 编译

## 7. 当前运行链路与部署阻塞点

### 阻塞点 1：后端主链路依赖线程 + jobs 目录

- 现状：提交接口只返回 job id，真正处理在后台线程中完成
- 风险：Vercel Functions 适合请求内完成，不适合维持本地式 job 生命周期
- 处理策略：改成同步解析、同步标准化、同步导出 zip；将 PDF 变为 local-only

### 阻塞点 2：状态持久化依赖本地文件系统

- 现状：`outputs/jobs` 与 `tmp/jobs` 是主状态来源
- 风险：Vercel 文件系统不应被当作持久存储
- 处理策略：线上主流程不保留服务端状态，只在请求内创建临时目录并直接返回结果

### 阻塞点 3：前端主流程围绕 job polling

- 现状：用户提交后跳到 job 详情页看状态
- 风险：主体验不适合普通学生，且与同步接口改造方向冲突
- 处理策略：改成四步向导：输入 → 解析 → 预览修正 → 导出

### 阻塞点 4：前后端 schema 不统一

- 现状：后端 schema 与前端 `web/src/types.ts` 分离维护
- 风险：改接口时容易漂移
- 处理策略：以后端 Pydantic schema 为唯一源，前端类型由脚本生成

### 阻塞点 5：项目结构不适合 Vercel 直接识别

- 现状：Python 配置在 `backend/`，前端静态文件由 FastAPI 挂载
- 风险：Vercel 难以直接把仓库识别为“静态前端 + Python API”
- 处理策略：新增根级 `pyproject.toml`、`index.py`、`vercel.json`、`public/`。Vercel 2026 年 FastAPI 文档要求在根级或 `src/` 等框架入口暴露 `app`，因此不采用 `api/index.py` 作为 FastAPI 主入口。
- 补充实测结论：在不使用 Vercel Services 的前提下，根级 FastAPI 入口会接管站点路由；因此首轮上线采用一个很薄的 FastAPI 静态 fallback，根路径返回构建生成的前端 HTML，`/assets/*` 返回前端资源，`/api/*` 继续作为 API。构建脚本会生成 `backend/app/frontend_bundle.py`，确保这些资源被打进 Python 函数包。这个方案牺牲了一部分静态 CDN 纯度，但避免引入 Services、数据库或后台队列，符合首轮最小可上线目标。

### 阻塞点 6：模板工作目录过胖

- 现状：`templates/working/latex-scnu-web/` 中有大量无关样例材料
- 风险：增大函数包与维护噪音
- 处理策略：瘦身为最小可生成模板集，但不动 `templates/upstream/`

### 阻塞点 7：线上 PDF 依赖不稳定

- 现状：当前 PDF 依赖本地 XeLaTeX 和本地文件系统
- 风险：若未经实测直接上线，会遇到时长、依赖、体积、稳定性、维护成本问题
- 处理策略：生产环境默认关闭 PDF，仅保留 `.tex` zip；PDF 能力保留在本地开发模式

### 阻塞点 8：部署上下文缺失

- 现状：机器上有 `vercel` CLI，但未登录，项目未 link
- 风险：无法直接创建预览部署
- 处理策略：代码整理完成后再执行 `vercel login`、`vercel link`、preview deploy

## 8. 首轮上线的真实产品边界

- 它是“结构识别 + 字段补全 + 章节预览 + 规范化导出”的工具型 web-app
- 它不是在线论文编辑器
- 它不是 Word 样式修复器
- 它不是学校官方系统的替代品
- 它可以帮助用户从内容进入模板，但不能代替人工校对最终格式
