import type { BodySection } from "../../generated/contracts";
import { EmptyState, FieldGroup, GhostDangerButton, SecondaryButton, SectionCard, StatusBadge } from "../../components/ui";

type SectionsEditorProps = {
  sections: BodySection[];
  onChange: (index: number, patch: Partial<BodySection>) => void;
  onAdd: () => void;
  onRemove: (index: number) => void;
};

export function SectionsEditor({ sections, onChange, onAdd, onRemove }: SectionsEditorProps) {
  return (
    <SectionCard
      title="正文章节"
      eyebrow="Body"
      description="这里决定论文结构骨架。请优先检查标题层级、章节命名和正文顺序。"
      tone="editor"
      action={
        <SecondaryButton type="button" onClick={onAdd}>
          新增章节
        </SecondaryButton>
      }
    >
      {sections.length === 0 ? (
        <EmptyState
          title="还没有识别到正文章节"
          message="可以手动新增章节，或回到输入区粘贴更完整的正文。"
          tone="warning"
          action={null}
        />
      ) : (
        <div className="chapter-stack">
          {sections.map((section, index) => {
            const prefix = `section-${section.id}-${index}`;
            return (
              <article className="chapter-card" key={section.id}>
                <div className="chapter-card-top">
                  <div className="chapter-card-title">
                    <div>
                      <p className="section-eyebrow">章节 {String(index + 1).padStart(2, "0")}</p>
                      <strong>{section.title.trim() || "未命名章节"}</strong>
                    </div>
                    <StatusBadge tone="info">{levelLabel(section.level)}</StatusBadge>
                  </div>

                  <div className="chapter-card-actions">
                    <FieldGroup label="层级" htmlFor={`${prefix}-level`}>
                      <select
                        id={`${prefix}-level`}
                        value={section.level}
                        onChange={(event) => onChange(index, { level: Number(event.target.value) })}
                      >
                        <option value={1}>一级标题</option>
                        <option value={2}>二级标题</option>
                        <option value={3}>三级标题</option>
                      </select>
                    </FieldGroup>
                    <GhostDangerButton type="button" onClick={() => onRemove(index)}>
                      删除章节
                    </GhostDangerButton>
                  </div>
                </div>
                <FieldGroup label="章节标题" htmlFor={`${prefix}-title`}>
                  <input
                    id={`${prefix}-title`}
                    value={section.title}
                    onChange={(event) => onChange(index, { title: event.target.value })}
                  />
                </FieldGroup>
                <FieldGroup label="章节内容" htmlFor={`${prefix}-content`}>
                  <textarea
                    id={`${prefix}-content`}
                    rows={8}
                    value={section.content}
                    onChange={(event) => onChange(index, { content: event.target.value })}
                  />
                </FieldGroup>
              </article>
            );
          })}
        </div>
      )}
    </SectionCard>
  );
}

function levelLabel(level: number) {
  return `H${level}`;
}
