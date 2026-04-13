import type { PrecheckIssue, PreviewBlock } from "../../generated/contracts";
import { issueText } from "../../app/domain";

type PreviewBlockCardProps = {
  block: PreviewBlock;
  issues: PrecheckIssue[];
};

export function PreviewBlockCard({ block, issues }: PreviewBlockCardProps) {
  return (
    <article className={`preview-block preview-block-${block.status}`}>
      <header className="preview-block-header">
        <div>
          <p>{block.label}</p>
          <h3>{block.preview}</h3>
        </div>
        <span className={`preview-badge preview-badge-${block.status}`}>
          {block.status === "blocking" ? "阻塞" : block.status === "warning" ? "警告" : "正常"}
        </span>
      </header>
      {issues.length > 0 ? (
        <ul className="preview-issues">
          {issues.map((issue) => (
            <li key={issue.id}>{issueText(issue)}</li>
          ))}
        </ul>
      ) : (
        <p className="preview-ok">当前块未发现阻塞问题。</p>
      )}
    </article>
  );
}
