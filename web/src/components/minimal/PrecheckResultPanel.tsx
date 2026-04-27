import type { PrecheckIssue, PrecheckResponse } from "../../generated/contracts";
import type { FlowPhase } from "../../app/domain";
import { WaveExportProgress } from "./WaveExportProgress";

type PrecheckResultPanelProps = {
  phase: FlowPhase;
  precheck: PrecheckResponse | null;
  fixApplied: boolean;
  exportProgress: number;
  exportMessage?: string;
  onApplyMockFix: () => void;
  onExport: () => void;
  onCancelExport: () => void;
};

const issueGroups = [
  { key: "structure", title: "结构问题", match: ["cover", "body", "appendices", "acknowledgements", "notes"] },
  { key: "heading", title: "标题层级问题", match: ["heading", "title", "body"] },
  { key: "abstract", title: "摘要 / 关键词问题", match: ["abstract", "keywords"] },
  { key: "font", title: "字体字号问题", match: ["font", "style", "format"] },
  { key: "spacing", title: "页边距 / 行距问题", match: ["margin", "spacing", "page"] },
  { key: "references", title: "参考文献格式问题", match: ["references", "reference"] },
];

export function PrecheckResultPanel({
  phase,
  precheck,
  fixApplied,
  exportProgress,
  exportMessage,
  onApplyMockFix,
  onExport,
  onCancelExport,
}: PrecheckResultPanelProps) {
  if (phase === "exporting") {
    return (
      <section id="export" className="result-panel result-panel-active" aria-label="导出进度">
        <div className="result-panel-heading">
          <span>Export</span>
          <h2>Exporting Word</h2>
          <p>正在基于当前预检结果生成 .docx 文件。</p>
        </div>
        <WaveExportProgress progress={exportProgress} message={exportMessage} onCancel={onCancelExport} />
      </section>
    );
  }

  if (phase === "analyzing") {
    return (
      <section id="export" className="result-panel result-panel-active" aria-live="polite" aria-label="正在分析">
        <div className="analysis-state">
          <span className="analysis-orb" />
          <div>
            <h2>Reading your thesis.</h2>
            <p>当前调用公开预检 API；格式要求解析与自动修复仍是后续 Agent 接入点。</p>
          </div>
        </div>
      </section>
    );
  }

  if (!precheck) {
    return (
      <section id="export" className="result-panel" aria-label="结果预览">
        <div className="result-panel-heading quiet-result">
          <span>Preview</span>
          <h2>Ready when your thesis is.</h2>
        </div>
      </section>
    );
  }

  const groupedIssues = buildIssueGroups(precheck.issues);
  const totalIssues = precheck.summary.blocking_count + precheck.summary.warning_count + precheck.summary.info_count;

  return (
    <section id="export" className="result-panel result-panel-active" aria-label="预检结果">
      <div className="result-panel-heading">
        <span>{fixApplied ? "Fixed Preview" : "Issues Found"}</span>
        <h2>{fixApplied ? "Fix flow reserved." : "Review before export."}</h2>
        <p>
          {fixApplied
            ? "当前为前端流程预览，后续可接入真实格式修复 Agent。"
            : totalIssues > 0
              ? `共识别 ${totalIssues} 项提示，导出前建议先查看问题。`
              : "结构主线已识别，未发现明显阻塞项。"}
        </p>
      </div>

      <div className="result-summary-strip">
        <span>Blocking {precheck.summary.blocking_count}</span>
        <span>Warnings {precheck.summary.warning_count}</span>
        <span>Notes {precheck.summary.info_count}</span>
      </div>

      <div id="precheck-issues" className="issue-group-grid">
        {groupedIssues.map((group) => (
          <article key={group.key} className="issue-group-card" data-empty={group.issues.length === 0}>
            <div>
              <h3>{group.title}</h3>
              <p>{group.issues[0]?.message ?? "当前未发现明显问题。"}</p>
            </div>
            <span>{group.issues.length}</span>
          </article>
        ))}
      </div>

      <div className="agent-boundary-note">
        检测结果仅用于辅助修改。自动修复策略与差异报告仍待接入真实 Agent API。
      </div>

      <div className="result-actions">
        <button type="button" className="secondary-action" onClick={onApplyMockFix} disabled={fixApplied}>
          Fix format
        </button>
        <button type="button" className="primary-action" onClick={onExport}>
          Export Word
        </button>
      </div>
    </section>
  );
}

function buildIssueGroups(issues: PrecheckIssue[]) {
  return issueGroups.map((group) => ({
    ...group,
    issues: issues.filter((issue) => {
      const haystack = `${issue.block} ${issue.code} ${issue.title}`.toLowerCase();
      return group.match.some((token) => haystack.includes(token));
    }),
  }));
}
