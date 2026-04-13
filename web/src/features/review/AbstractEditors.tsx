import type { SummarySection } from "../../generated/contracts";
import { keywordsToString, splitKeywords } from "../../app/domain";
import { FieldGroup, SectionCard } from "../../components/ui";

type AbstractEditorsProps = {
  abstractCn: SummarySection;
  abstractEn: SummarySection;
  onChange: (kind: "cn" | "en", patch: Partial<SummarySection>) => void;
};

export function AbstractEditors({ abstractCn, abstractEn, onChange }: AbstractEditorsProps) {
  return (
    <div className="editor-grid">
      <SectionCard title="中文摘要" eyebrow="Abstract CN" tone="editor" description="检查摘要正文和关键词，避免导出后再回头修改。">
        <FieldGroup label="摘要" htmlFor="abstract-cn-content">
          <textarea
            id="abstract-cn-content"
            rows={8}
            value={abstractCn.content}
            onChange={(event) => onChange("cn", { content: event.target.value })}
          />
        </FieldGroup>
        <FieldGroup label="关键词" htmlFor="abstract-cn-keywords" hint="用分号、逗号或换行分隔。">
          <input
            id="abstract-cn-keywords"
            value={keywordsToString(abstractCn.keywords)}
            onChange={(event) => onChange("cn", { keywords: splitKeywords(event.target.value) })}
          />
        </FieldGroup>
      </SectionCard>

      <SectionCard title="Abstract" eyebrow="Abstract EN" tone="editor" description="英文摘要建议与中文摘要的结构保持一致。">
        <FieldGroup label="Abstract" htmlFor="abstract-en-content">
          <textarea
            id="abstract-en-content"
            rows={8}
            value={abstractEn.content}
            onChange={(event) => onChange("en", { content: event.target.value })}
          />
        </FieldGroup>
        <FieldGroup label="Keywords" htmlFor="abstract-en-keywords" hint="Use semicolons, commas, or line breaks.">
          <input
            id="abstract-en-keywords"
            value={keywordsToString(abstractEn.keywords)}
            onChange={(event) => onChange("en", { keywords: splitKeywords(event.target.value) })}
          />
        </FieldGroup>
      </SectionCard>
    </div>
  );
}
