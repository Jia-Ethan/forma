import { useRef, useState } from "react";
import type { FlowPhase, InlineErrorState } from "../../app/domain";
import { HeroAmbient } from "./HeroAmbient";
import { HomeComposer } from "./HomeComposer";
import { InlineError } from "./InlineError";

type MinimalHomeProps = {
  rawText: string;
  selectedFile: File | null;
  phase: FlowPhase;
  exportProgress: number;
  error: InlineErrorState | null;
  privacyAccepted: boolean;
  turnstileToken: string;
  onTextChange: (value: string) => void;
  onUploadTrigger: () => boolean;
  onFileSelect: (file: File | null) => void;
  onSubmit: () => void;
  onClear: () => void;
  onPrivacyAcceptedChange: (value: boolean) => void;
  onTurnstileTokenChange: (value: string) => void;
};

export function MinimalHome(props: MinimalHomeProps) {
  const heroRef = useRef<HTMLElement | null>(null);
  const [isDragActive, setIsDragActive] = useState(false);
  const hasContent = Boolean(props.selectedFile || props.rawText.trim());
  const isBusy = props.phase === "prechecking" || props.phase === "exporting";

  return (
    <main className="public-page">
      <section
        ref={heroRef}
        className="public-hero minimal-hero"
        aria-labelledby="sc-th-title"
        data-has-content={hasContent}
        data-drag-active={isDragActive}
        data-busy={isBusy}
      >
        <HeroAmbient containerRef={heroRef} />
        <img className="public-hero-image" src="/product/workbench-preview.png" alt="" aria-hidden="true" />
        <div className="public-hero-copy">
          <p className="public-kicker">SCNU Thesis Agent Workbench</p>
          <h1 id="sc-th-title" className="minimal-logo">
            华师本科论文格式合规与版本工作台
          </h1>
          <p className="public-subtitle">
            把论文材料、格式检查、老师批注、建议队列、版本和导出放进同一个可追溯项目空间。公开站只做快速格式预检与 Word 导出，不启用远程 AI。
          </p>
          <nav className="public-hero-actions" aria-label="首页快捷入口">
            <a href="#quick-export">在线快速导出</a>
            <a href="#/workbench-demo">查看 Workbench</a>
            <a href="#/en">English</a>
            <a href="https://github.com/Jia-Ethan/scnu-thesis-portal" target="_blank" rel="noreferrer">GitHub</a>
            <a href="#self-host">本地部署</a>
          </nav>
        </div>
        <section id="quick-export" className="public-export-panel" aria-label="在线快速导出">
          <div className="public-export-copy">
            <p className="public-kicker">Public demo</p>
            <h2>上传 .docx 或粘贴已有论文正文，先做格式预检，再导出规范化 Word。</h2>
          </div>
          <HomeComposer
            rawText={props.rawText}
            selectedFile={props.selectedFile}
            phase={props.phase}
            exportProgress={props.exportProgress}
            privacyAccepted={props.privacyAccepted}
            turnstileToken={props.turnstileToken}
            onTextChange={props.onTextChange}
            onUploadTrigger={props.onUploadTrigger}
            onFileSelect={props.onFileSelect}
            onSubmit={props.onSubmit}
            onClear={props.onClear}
            onDragActiveChange={setIsDragActive}
            onPrivacyAcceptedChange={props.onPrivacyAcceptedChange}
            onTurnstileTokenChange={props.onTurnstileTokenChange}
          />
          <InlineError message={props.error?.message ?? null} />
        </section>
      </section>

      <section className="public-section public-flow" aria-labelledby="demo-flow-title">
        <div className="public-section-head">
          <p className="public-kicker">Demo flow</p>
          <h2 id="demo-flow-title">从上传到合规导出，公开站只保留低风险主线。</h2>
        </div>
        <div className="public-flow-grid">
          {demoFlow.map((item) => (
            <article key={item.title} className="public-flow-step">
              <span>{item.index}</span>
              <h3>{item.title}</h3>
              <p>{item.description}</p>
            </article>
          ))}
        </div>
        <img className="public-wide-image" src="/product/precheck.png" alt="导出前结构预检界面截图" />
      </section>

      <section className="public-section public-workbench" aria-labelledby="workbench-title">
        <div className="public-section-head">
          <p className="public-kicker">Workbench preview</p>
          <h2 id="workbench-title">完整 Workbench 面向私有部署，公开站提供安全预览。</h2>
          <p>项目空间会保存文件库、当前版本、版本历史、Proposal Queue、导出记录、审计日志和 Provider 授权状态。</p>
        </div>
        <div className="public-workbench-grid">
          <img src="/product/workbench-preview.png" alt="Workbench 项目空间预览截图" />
          <div className="public-capability-list">
            {workbenchCapabilities.map((item) => (
              <article key={item.title}>
                <h3>{item.title}</h3>
                <p>{item.description}</p>
              </article>
            ))}
            <a className="public-primary-link" href="#/workbench-demo">打开示例项目</a>
          </div>
        </div>
      </section>

      <section className="public-section public-boundary" aria-labelledby="privacy-title">
        <div>
          <p className="public-kicker">Privacy boundary</p>
          <h2 id="privacy-title">公开站不调用远程 AI，也不长期保存正文。</h2>
        </div>
        <div className="public-boundary-grid">
          {privacyRules.map((item) => (
            <article key={item.title}>
              <h3>{item.title}</h3>
              <p>{item.description}</p>
            </article>
          ))}
        </div>
      </section>

      <section id="self-host" className="public-section public-self-host" aria-labelledby="self-host-title">
        <div className="public-section-head">
          <p className="public-kicker">Self-host</p>
          <h2 id="self-host-title">敏感论文建议本地或私有部署。</h2>
          <p>Vercel 只保留静态 mirror；完整 Workbench、访问码保护、Provider key 服务端封存和 Ollama 本地模型更适合私有环境。</p>
        </div>
        <pre aria-label="本地部署命令"><code>{`uv sync --extra dev
npm install --prefix web
docker compose up --build`}</code></pre>
      </section>

      <section className="public-section public-roadmap" aria-labelledby="roadmap-title">
        <div className="public-section-head">
          <p className="public-kicker">Roadmap</p>
          <h2 id="roadmap-title">先完成公开可信度，再进入真实 Agent Runtime。</h2>
        </div>
        <ol>
          {roadmapItems.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ol>
      </section>
    </main>
  );
}

const demoFlow = [
  { index: "01", title: "上传材料", description: "上传 .docx 或粘贴已有论文正文，快速进入结构识别。" },
  { index: "02", title: "结构预检", description: "检查摘要、目录、正文、参考文献和复杂元素风险。" },
  { index: "03", title: "合规导出", description: "按华师本科论文规范生成 Word 文档，保留人工复核提示。" },
  { index: "04", title: "继续 Workbench", description: "需要版本、批注和建议队列时，进入私有项目空间。" },
];

const workbenchCapabilities = [
  { title: "Project Workspace", description: "材料、版本、导出、Issue Ledger 与 Audit Log 放在同一个项目中。" },
  { title: "Proposal Queue", description: "AI 或规则候选只进入建议队列，用户确认后才生成新版本。" },
  { title: "Provider Boundary", description: "前端只看到模型能力与验证状态，不接触 API key 和原始密钥配置。" },
  { title: "Local-first", description: "默认本地优先；远程 Provider 必须经过项目级授权。" },
];

const privacyRules = [
  { title: "非官方系统", description: "项目不代表学校官方入口，规范实现以公开手册和模板为依据。" },
  { title: "非代写定位", description: "公开文案只强调协作写作、格式合规、审稿处理和版本管理。" },
  { title: "不承诺查重率", description: "不会预测查重率，也不会伪造参考文献、实验数据或来源事实。" },
  { title: "远程 AI 关闭", description: "公开站不开放匿名远程 Provider；敏感论文建议私有部署。" },
];

const roadmapItems = [
  "Phase 0: Vercel 静态 mirror / 生产入口解耦",
  "Phase 1: 国内云主站 / Caddy HTTPS / Postgres",
  "Phase 2: 匿名 .docx 快速导出 / Turnstile / 限流",
  "Phase 3: Workbench Demo / Access-code MVP",
  "Phase 4: CI smoke / uptime / 备份恢复",
];
