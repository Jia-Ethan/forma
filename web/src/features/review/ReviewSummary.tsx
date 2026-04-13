import type { NormalizedThesis } from "../../generated/contracts";
import type { ExportReadiness } from "../../app/domain";
import { bodySummary, reviewCompletion, reviewInsights } from "../../app/domain";
import { InfoNotice, SectionCard, StatusBadge } from "../../components/ui";

type ReviewSummaryProps = {
  thesis: NormalizedThesis;
  readiness: ExportReadiness;
};

export function ReviewSummary({ thesis, readiness }: ReviewSummaryProps) {
  const summary = bodySummary(thesis);
  const completion = reviewCompletion(thesis, readiness);
  const insights = reviewInsights(thesis, readiness);

  return (
    <SectionCard title="识别概览" eyebrow="Review" description="先看整体完成度，再决定先修哪里、什么时候导出。" tone="accent">
      <div className="completion-meter" aria-label={`当前完成度 ${completion.percent}%`}>
        <div className="completion-meter-bar">
          <span style={{ width: `${completion.percent}%` }} />
        </div>
        <div className="completion-meter-copy">
          <strong>{completion.percent}%</strong>
          <p>{completion.done} / {completion.total} 项检查点已完成</p>
        </div>
      </div>

      <div className="review-summary-meta">
        <div>
          <span>必填缺口</span>
          <strong>{completion.missingRequired}</strong>
        </div>
        <div>
          <span>建议补全</span>
          <strong>{completion.missingRecommended}</strong>
        </div>
        <div>
          <span>正文章节</span>
          <strong>{summary.bodyCount}</strong>
        </div>
      </div>

      <div className="summary-list">
        <SummaryRow label="中文摘要" value={summary.abstractCn ? "已识别" : "待补充"} done={summary.abstractCn} />
        <SummaryRow label="Abstract" value={summary.abstractEn ? "已识别" : "待补充"} done={summary.abstractEn} />
        <SummaryRow label="正文章节" value={`${summary.bodyCount} 个`} done={summary.bodyCount > 0} />
        <SummaryRow label="参考文献" value={`${summary.referencesCount} 条`} done={summary.referencesCount > 0} />
        <SummaryRow label="致谢" value={summary.acknowledgements ? "已识别" : "待补充"} done={summary.acknowledgements} />
        <SummaryRow label="附录" value={summary.appendix ? "已识别" : "待补充"} done={summary.appendix} />
      </div>

      <div className="review-insight-list">
        {insights.map((item) => (
          <InfoNotice key={item.title} title={item.title} tone={item.tone}>
            <p>{item.message}</p>
          </InfoNotice>
        ))}
      </div>

      {thesis.warnings.length > 0 ? (
        <InfoNotice title="需要留意" tone="warning">
          <ul className="plain-list">
            {thesis.warnings.map((warning) => (
              <li key={warning}>{warning}</li>
            ))}
          </ul>
        </InfoNotice>
      ) : null}

      {thesis.parse_errors.length > 0 ? (
        <InfoNotice title="解析提示" tone="danger">
          <ul className="plain-list">
            {thesis.parse_errors.map((message) => (
              <li key={message}>{message}</li>
            ))}
          </ul>
        </InfoNotice>
      ) : null}
    </SectionCard>
  );
}

function SummaryRow({ label, value, done }: { label: string; value: string; done: boolean }) {
  return (
    <div className="summary-row">
      <span>{label}</span>
      <StatusBadge tone={done ? "success" : "warning"}>{value}</StatusBadge>
    </div>
  );
}
