import { useEffect, useState, type FormEvent } from "react";
import type { ProjectDraft, ThesisProject } from "../app/api";

type ProjectSettingsProps = {
  project: ThesisProject | null;
  busy?: boolean;
  onSave: (patch: Partial<ProjectDraft>) => Promise<void>;
};

export function ProjectSettings({ project, busy = false, onSave }: ProjectSettingsProps) {
  const [draft, setDraft] = useState<Partial<ProjectDraft>>({});

  useEffect(() => {
    if (!project) return;
    setDraft({
      title: project.title,
      department: project.department,
      major: project.major,
      advisor: project.advisor,
      student_name: project.student_name,
      student_id: project.student_id,
      writing_stage: project.writing_stage,
      privacy_mode: project.privacy_mode,
      remote_provider_allowed: project.remote_provider_allowed,
    });
  }, [project]);

  if (!project) return null;

  function update<K extends keyof ProjectDraft>(key: K, value: ProjectDraft[K]) {
    setDraft((current) => {
      const next = { ...current, [key]: value };
      if (key === "privacy_mode" && value === "local_only") {
        next.remote_provider_allowed = false;
      }
      return next;
    });
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await onSave({
      ...draft,
      remote_provider_allowed: draft.privacy_mode === "remote_allowed" && !!draft.remote_provider_allowed,
    });
  }

  return (
    <form className="project-settings" onSubmit={(event) => void handleSubmit(event)}>
      <h3>项目设置</h3>
      <label>
        论文题目
        <input value={draft.title ?? ""} onChange={(event) => update("title", event.target.value)} />
      </label>
      <div className="workbench-form-grid">
        <label>
          学院
          <input value={draft.department ?? ""} onChange={(event) => update("department", event.target.value)} />
        </label>
        <label>
          专业
          <input value={draft.major ?? ""} onChange={(event) => update("major", event.target.value)} />
        </label>
        <label>
          指导老师
          <input value={draft.advisor ?? ""} onChange={(event) => update("advisor", event.target.value)} />
        </label>
        <label>
          写作阶段
          <select value={draft.writing_stage ?? "draft"} onChange={(event) => update("writing_stage", event.target.value)}>
            <option value="topic">选题</option>
            <option value="proposal">开题</option>
            <option value="draft">初稿</option>
            <option value="revision">修改</option>
            <option value="final_check">定稿自检</option>
          </select>
        </label>
      </div>
      <fieldset className="privacy-choice">
        <legend>远程模型授权</legend>
        <label>
          <input type="radio" checked={(draft.privacy_mode ?? "local_only") === "local_only"} onChange={() => update("privacy_mode", "local_only")} />
          本地优先
        </label>
        <label>
          <input type="radio" checked={draft.privacy_mode === "remote_allowed"} onChange={() => update("privacy_mode", "remote_allowed")} />
          允许远程 Provider
        </label>
        <label className="checkbox-line">
          <input
            type="checkbox"
            checked={!!draft.remote_provider_allowed}
            disabled={draft.privacy_mode !== "remote_allowed"}
            onChange={(event) => update("remote_provider_allowed", event.target.checked)}
          />
          确认远程处理提示
        </label>
      </fieldset>
      <button type="submit" disabled={busy}>
        保存项目设置
      </button>
    </form>
  );
}
