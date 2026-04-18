import { useState, type FormEvent } from "react";
import type { ProjectDraft } from "../app/api";

type ProjectWizardProps = {
  onCreate: (draft: ProjectDraft) => Promise<void>;
  busy?: boolean;
};

const DEFAULT_DRAFT: ProjectDraft = {
  title: "",
  department: "",
  major: "",
  advisor: "",
  student_name: "",
  student_id: "",
  writing_stage: "draft",
  privacy_mode: "local_only",
  remote_provider_allowed: false,
};

export function ProjectWizard({ onCreate, busy = false }: ProjectWizardProps) {
  const [draft, setDraft] = useState<ProjectDraft>(DEFAULT_DRAFT);

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
    await onCreate({
      ...draft,
      title: draft.title.trim() || "未命名论文项目",
      remote_provider_allowed: draft.privacy_mode === "remote_allowed" && !!draft.remote_provider_allowed,
    });
    setDraft(DEFAULT_DRAFT);
  }

  return (
    <form className="project-wizard" onSubmit={(event) => void handleSubmit(event)}>
      <label>
        论文题目
        <input value={draft.title} onChange={(event) => update("title", event.target.value)} placeholder="输入论文题目" />
      </label>
      <div className="workbench-form-grid">
        <label>
          学院
          <input value={draft.department} onChange={(event) => update("department", event.target.value)} />
        </label>
        <label>
          专业
          <input value={draft.major} onChange={(event) => update("major", event.target.value)} />
        </label>
        <label>
          指导老师
          <input value={draft.advisor} onChange={(event) => update("advisor", event.target.value)} />
        </label>
        <label>
          学生姓名
          <input value={draft.student_name} onChange={(event) => update("student_name", event.target.value)} />
        </label>
        <label>
          学号
          <input value={draft.student_id} onChange={(event) => update("student_id", event.target.value)} />
        </label>
        <label>
          写作阶段
          <select value={draft.writing_stage} onChange={(event) => update("writing_stage", event.target.value)}>
            <option value="topic">选题</option>
            <option value="proposal">开题</option>
            <option value="draft">初稿</option>
            <option value="revision">修改</option>
            <option value="final_check">定稿自检</option>
          </select>
        </label>
      </div>
      <fieldset className="privacy-choice">
        <legend>隐私模式</legend>
        <label>
          <input type="radio" checked={draft.privacy_mode === "local_only"} onChange={() => update("privacy_mode", "local_only")} />
          本地优先，不发送真实正文到远程模型
        </label>
        <label>
          <input type="radio" checked={draft.privacy_mode === "remote_allowed"} onChange={() => update("privacy_mode", "remote_allowed")} />
          允许远程 Provider 处理经确认的任务内容
        </label>
        <label className="checkbox-line">
          <input
            type="checkbox"
            checked={!!draft.remote_provider_allowed}
            disabled={draft.privacy_mode !== "remote_allowed"}
            onChange={(event) => update("remote_provider_allowed", event.target.checked)}
          />
          我理解远程模型会离开本机处理内容
        </label>
      </fieldset>
      <button type="submit" disabled={busy}>
        创建项目
      </button>
    </form>
  );
}
