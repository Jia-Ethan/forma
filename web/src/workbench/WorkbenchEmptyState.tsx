import type { ReactNode } from "react";

type WorkbenchEmptyStateProps = {
  children: ReactNode;
};

export function WorkbenchEmptyState({ children }: WorkbenchEmptyStateProps) {
  return (
    <section className="workbench-empty-state">
      <div>
        <p className="eyebrow">Project workspace</p>
        <h2>先建立一个可追溯的论文项目</h2>
        <p>项目会保存材料、版本、建议队列、导出历史和审计记录。AI 候选内容不会直接写入当前版本。</p>
      </div>
      {children}
    </section>
  );
}
