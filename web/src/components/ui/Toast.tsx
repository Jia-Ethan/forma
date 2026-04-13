import type { ToastState } from "../../app/domain";

type ToastProps = {
  toast: ToastState;
  onDismiss: () => void;
};

export function Toast({ toast, onDismiss }: ToastProps) {
  if (!toast) return null;

  return (
    <div className={`toast toast-${toast.tone}`} role={toast.tone === "danger" ? "alert" : "status"} aria-live="polite">
      <div>
        <strong>{toast.title}</strong>
        <p>{toast.message}</p>
      </div>
      <button type="button" aria-label="关闭提示" onClick={onDismiss}>
        关闭
      </button>
    </div>
  );
}
