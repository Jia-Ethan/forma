import type { BodySection, MetadataFields, NormalizedThesis, SummarySection } from "../../generated/contracts";
import type { ExportReadiness } from "../../app/domain";
import { AbstractEditors } from "./AbstractEditors";
import { AppendixEditor } from "./AppendixEditor";
import { MetadataEditor } from "./MetadataEditor";
import { ReferencesEditor } from "./ReferencesEditor";
import { SectionsEditor } from "./SectionsEditor";

type ReviewWorkspaceProps = {
  thesis: NormalizedThesis;
  readiness: ExportReadiness;
  updateMetadata: (field: keyof MetadataFields, value: string) => void;
  updateAbstract: (kind: "cn" | "en", patch: Partial<SummarySection>) => void;
  updateSection: (index: number, patch: Partial<BodySection>) => void;
  addSection: () => void;
  removeSection: (index: number) => void;
  updateReferences: (items: string[]) => void;
  updateLongText: (field: "acknowledgements" | "appendix", value: string) => void;
};

export function ReviewWorkspace({
  thesis,
  readiness,
  updateMetadata,
  updateAbstract,
  updateSection,
  addSection,
  removeSection,
  updateReferences,
  updateLongText,
}: ReviewWorkspaceProps) {
  return (
    <div className="review-workspace" aria-label="论文内容校对区">
      <MetadataEditor metadata={thesis.metadata} readiness={readiness} onChange={updateMetadata} />
      <AbstractEditors abstractCn={thesis.abstract_cn} abstractEn={thesis.abstract_en} onChange={updateAbstract} />
      <SectionsEditor sections={thesis.body_sections} onChange={updateSection} onAdd={addSection} onRemove={removeSection} />
      <div className="review-support-grid">
        <ReferencesEditor thesis={thesis} onChange={updateReferences} />
        <AppendixEditor acknowledgements={thesis.acknowledgements} appendix={thesis.appendix} onChange={updateLongText} />
      </div>
    </div>
  );
}
