import type { MetadataFields } from "../../generated/contracts";
import type { ExportReadiness } from "../../app/domain";
import { metadataFieldRules } from "../../app/domain";
import { FieldGroup, SectionCard, StatusBadge } from "../../components/ui";

type MetadataEditorProps = {
  metadata: MetadataFields;
  readiness: ExportReadiness;
  onChange: (field: keyof MetadataFields, value: string) => void;
};

export function MetadataEditor({ metadata, readiness, onChange }: MetadataEditorProps) {
  const missingRequired = new Set(readiness.missingRequired.map((item) => item.field));
  const missingRecommended = new Set(readiness.missingRecommended.map((item) => item.field));
  const completed = metadataFieldRules.length - readiness.missingRequired.length - readiness.missingRecommended.length;

  return (
    <SectionCard
      title="封面字段"
      eyebrow="Metadata"
      description="这些字段会进入模板工程，也是导出前最需要确认的一组信息。"
      tone="feature"
      action={<StatusBadge tone={readiness.canExport ? "success" : "warning"}>{completed}/{metadataFieldRules.length} 已补齐</StatusBadge>}
    >
      <div className="form-grid">
        {metadataFieldRules.map(({ field, label, required }) => {
          const id = `metadata-${field}`;
          const isMissingRequired = missingRequired.has(field);
          const isMissingRecommended = missingRecommended.has(field);
          return (
            <FieldGroup
              key={field}
              label={label}
              htmlFor={id}
              hint={required ? "导出前必填" : "建议补全，不阻塞导出"}
              error={isMissingRequired ? "必填字段待补齐" : undefined}
            >
              <div className="field-with-status">
                <StatusBadge tone={required ? (isMissingRequired ? "warning" : "success") : isMissingRecommended ? "info" : "success"}>
                  {required ? (isMissingRequired ? "必填" : "已填") : isMissingRecommended ? "建议" : "已填"}
                </StatusBadge>
              </div>
              <input id={id} value={metadata[field] ?? ""} onChange={(event) => onChange(field, event.target.value)} />
            </FieldGroup>
          );
        })}
      </div>
    </SectionCard>
  );
}
