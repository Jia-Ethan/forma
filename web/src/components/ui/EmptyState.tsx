import type { ReactNode } from "react";

type EmptyStateProps = {
  title: string;
  message: string;
  action?: ReactNode;
  tone?: "default" | "info" | "warning";
};

export function EmptyState({ title, message, action, tone = "default" }: EmptyStateProps) {
  return (
    <div className={`empty-state empty-state-${tone}`}>
      <p className="empty-state-title">{title}</p>
      <p>{message}</p>
      {action ? <div className="empty-state-action">{action}</div> : null}
    </div>
  );
}
