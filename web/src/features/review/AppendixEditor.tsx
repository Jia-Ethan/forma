import { FieldGroup, SectionCard } from "../../components/ui";

type AppendixEditorProps = {
  acknowledgements: string;
  appendix: string;
  onChange: (field: "acknowledgements" | "appendix", value: string) => void;
};

export function AppendixEditor({ acknowledgements, appendix, onChange }: AppendixEditorProps) {
  return (
    <SectionCard title="致谢与附录" eyebrow="Closing Sections" tone="muted" description="收尾内容可以晚一点补，但导出前建议至少快速核对一次。">
      <div className="editor-grid">
        <FieldGroup label="致谢" htmlFor="acknowledgements">
          <textarea
            id="acknowledgements"
            rows={6}
            value={acknowledgements}
            onChange={(event) => onChange("acknowledgements", event.target.value)}
          />
        </FieldGroup>
        <FieldGroup label="附录" htmlFor="appendix">
          <textarea id="appendix" rows={6} value={appendix} onChange={(event) => onChange("appendix", event.target.value)} />
        </FieldGroup>
      </div>
    </SectionCard>
  );
}
