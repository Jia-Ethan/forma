import type { PrecheckResponse } from "../../generated/contracts";
import { PreviewBlockCard } from "./PreviewBlockCard";

type PrecheckModalProps = {
  open: boolean;
  precheck: PrecheckResponse | null;
  onCancel: () => void;
  onConfirm: () => void;
};

export function PrecheckModal({ open, precheck, onCancel, onConfirm }: PrecheckModalProps) {
  if (!open || !precheck) return null;

  const issueMap = new Map(precheck.issues.map((issue) => [issue.id, issue]));
  const blockingIssues = precheck.issues.filter((issue) => issue.severity === "blocking");
  const infoIssues = precheck.issues.filter((issue) => issue.severity === "info");

  return (
    <div className="modal-overlay" role="presentation">
      <div className="precheck-modal" role="dialog" aria-modal="true" aria-labelledby="precheck-title">
        <div className="precheck-modal-top">
          <div>
            <p className="precheck-eyebrow">预检确认</p>
            <h2 id="precheck-title">导出前结构预检</h2>
          </div>
          <button type="button" className="modal-close" onClick={onCancel} aria-label="关闭预检弹窗">
            ×
          </button>
        </div>

        <div className={`precheck-summary ${precheck.summary.can_confirm ? "precheck-summary-pass" : "precheck-summary-block"}`}>
          <strong>{precheck.summary.blocking_message}</strong>
          <p>{precheck.summary.warning_message}</p>
        </div>

        <div className="precheck-grid">
          {precheck.preview_blocks.map((block) => (
            <PreviewBlockCard key={block.key} block={block} issues={block.issue_ids.map((id) => issueMap.get(id)).filter(Boolean) as typeof precheck.issues} />
          ))}
        </div>

        <div className="precheck-footer">
          <div className="precheck-footer-copy">
            <p>
              阻塞项 {blockingIssues.length} / 警告项 {precheck.summary.warning_count} / 信息项 {infoIssues.length}
            </p>
            {precheck.summary.warning_count > 0 ? <small>{precheck.summary.warning_message}</small> : null}
          </div>
          <div className="precheck-footer-actions">
            <button type="button" className="button button-subtle" onClick={onCancel}>
              取消
            </button>
            <button type="button" className="button button-primary" onClick={onConfirm} disabled={!precheck.summary.can_confirm}>
              {precheck.summary.can_confirm ? "确认并导出" : `仍有 ${precheck.summary.blocking_count} 项未满足`}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
