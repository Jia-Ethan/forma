import type { HealthResponse } from "../../generated/contracts";
import { StatusBadge } from "../../components/ui";

type CapabilitySummaryProps = {
  health: HealthResponse | null;
  compact?: boolean;
};

export function CapabilitySummary({ health, compact = false }: CapabilitySummaryProps) {
  const pdfEnabled = Boolean(health?.capabilities.pdf);

  return (
    <dl className={compact ? "capability-summary capability-summary-compact" : "capability-summary"}>
      <div className="capability-item">
        <dt>模板</dt>
        <dd>
          <div className="capability-item-main">
            <strong>{health?.template ?? "加载中"}</strong>
            <StatusBadge tone={health?.template ? "success" : "info"}>{health?.template ? "已就绪" : "加载中"}</StatusBadge>
          </div>
          <p>当前主线模板工程。</p>
        </dd>
      </div>
      <div className="capability-item">
        <dt>主产物</dt>
        <dd>
          <div className="capability-item-main">
            <strong>.tex 工程 zip</strong>
            <StatusBadge tone="success">主路径</StatusBadge>
          </div>
          <p>适合下载后本地编译或继续人工调整。</p>
        </dd>
      </div>
      <div className="capability-item">
        <dt>PDF</dt>
        <dd>
          <div className="capability-item-main">
            <strong>{pdfEnabled ? "已开启" : "未开启"}</strong>
            <StatusBadge tone={pdfEnabled ? "success" : "warning"}>{pdfEnabled ? "可导出" : "受限"}</StatusBadge>
          </div>
          <p>{health?.capabilities.pdf_reason ?? "生产环境默认关闭 PDF，请导出 tex 工程 zip。"}</p>
        </dd>
      </div>
    </dl>
  );
}
