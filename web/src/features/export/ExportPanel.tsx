import type { NormalizedThesis } from "../../generated/contracts";
import type { ExportKind, ExportReadiness } from "../../app/domain";
import { InfoNotice, PrimaryButton, SecondaryButton, SectionCard, StatusBadge } from "../../components/ui";

type ExportPanelProps = {
  thesis: NormalizedThesis;
  readiness: ExportReadiness;
  exporting: ExportKind | null;
  onExport: (kind: ExportKind) => void;
};

export function ExportPanel({ thesis, readiness, exporting, onExport }: ExportPanelProps) {
  const pdfEnabled = thesis.capabilities.pdf;

  return (
    <SectionCard
      title="导出成果"
      eyebrow="最终产物"
      description="把导出当成一次提交动作：先看阻塞项，再决定是否生成产物。"
      className="export-panel"
      tone="critical"
    >
      <div className="export-product">
        <div>
          <p className="export-product-label">推荐导出</p>
          <h3>.tex 工程 zip</h3>
          <p>包含 normalized 内容映射后的模板工程，适合本地编译或人工继续修正。</p>
        </div>
        <StatusBadge tone="success">主路径</StatusBadge>
      </div>

      <div className="export-readiness">
        <div>
          <span>导出状态</span>
          <strong>{readiness.canExport ? "可以导出" : "仍需补齐字段"}</strong>
        </div>
        <div>
          <span>必填字段</span>
          <strong>{readiness.missingRequired.length === 0 ? "已完成" : `缺 ${readiness.missingRequired.length} 项`}</strong>
        </div>
        <div>
          <span>建议检查</span>
          <strong>{readiness.missingRecommended.length === 0 ? "已完成" : `${readiness.missingRecommended.length} 项`}</strong>
        </div>
      </div>

      <div className="export-actions">
        <PrimaryButton type="button" onClick={() => onExport("tex")} disabled={exporting !== null || !readiness.canExport}>
          {readiness.canExport ? (exporting === "tex" ? "正在生成 zip" : "导出 .tex 工程 zip") : "补全必填字段后导出"}
        </PrimaryButton>
        <SecondaryButton type="button" onClick={() => onExport("pdf")} disabled={!pdfEnabled || exporting !== null}>
          {exporting === "pdf" ? "正在生成 PDF" : "导出 PDF"}
        </SecondaryButton>
      </div>

      {!readiness.canExport ? (
        <InfoNotice title="导出前还缺必填字段" tone="warning">
          <p>{readiness.missingRequired.map((field) => field.label).join("、")} 需要补齐后才能导出 .tex 工程 zip。</p>
        </InfoNotice>
      ) : readiness.missingRecommended.length > 0 ? (
        <InfoNotice title="建议补全" tone="info">
          <p>{readiness.missingRecommended.map((field) => field.label).join("、")} 不是阻塞项，但补齐后模板信息会更完整。</p>
        </InfoNotice>
      ) : null}

      {!pdfEnabled ? (
        <InfoNotice title="PDF 当前未开启" tone="warning">
          <p>{thesis.capabilities.pdf_reason ?? "生产环境默认关闭 PDF，请先导出 tex 工程 zip。"}</p>
          <p>建议路径：下载 zip 后，在本地 TeX 环境中编译并人工检查格式。</p>
        </InfoNotice>
      ) : null}
    </SectionCard>
  );
}
