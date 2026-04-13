import { useId, useLayoutEffect, useMemo, useRef } from "react";
import type { FlowPhase } from "../../app/domain";
import { WaveExportProgress } from "./WaveExportProgress";

type HomeComposerProps = {
  rawText: string;
  selectedFile: File | null;
  phase: FlowPhase;
  exportProgress: number;
  onTextChange: (value: string) => void;
  onUploadTrigger: () => boolean;
  onFileSelect: (file: File | null) => void;
  onSubmit: () => void;
  onClear: () => void;
};

export function HomeComposer({ rawText, selectedFile, phase, exportProgress, onTextChange, onUploadTrigger, onFileSelect, onSubmit, onClear }: HomeComposerProps) {
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);
  const fileInputId = useId();
  const hasContent = Boolean(selectedFile || rawText.trim());
  const disabled = phase === "prechecking" || phase === "exporting";

  const placeholder = useMemo(() => {
    if (selectedFile) return selectedFile.name;
    return "上传 .docx 或粘贴论文内容";
  }, [selectedFile]);

  useLayoutEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea || selectedFile) return;

    textarea.style.height = "0px";
    const computed = window.getComputedStyle(textarea);
    const fontSize = Number.parseFloat(computed.fontSize) || 16;
    const rawLineHeight = Number.parseFloat(computed.lineHeight);
    const lineHeight = computed.lineHeight.endsWith("px")
      ? rawLineHeight || fontSize * 1.5
      : rawLineHeight && rawLineHeight > 0 && rawLineHeight < 3
        ? fontSize * rawLineHeight
        : fontSize * 1.5;
    const minHeight = Math.ceil(lineHeight);
    const maxHeight = Math.ceil(lineHeight * 4 + 4);
    const nextHeight = Math.min(Math.max(textarea.scrollHeight, minHeight), maxHeight);

    textarea.style.height = `${nextHeight}px`;
    textarea.style.overflowY = textarea.scrollHeight > maxHeight ? "auto" : "hidden";
  }, [rawText, selectedFile, phase]);

  return (
    <div className="composer-shell">
      <div className={`composer ${selectedFile ? "composer-file" : ""} ${disabled ? "composer-busy" : ""}`} tabIndex={selectedFile ? 0 : -1} onKeyDown={(event) => {
        if (!selectedFile || disabled) return;
        if (event.key === "Enter") {
          event.preventDefault();
          onSubmit();
        }
      }}>
        <label
          htmlFor={disabled ? undefined : fileInputId}
          className="composer-plus"
          aria-label="上传 .docx 文件"
          aria-disabled={disabled ? "true" : undefined}
          role="button"
          tabIndex={disabled ? -1 : 0}
          onClick={(event) => {
            if (disabled || !onUploadTrigger()) {
              event.preventDefault();
            }
          }}
          onKeyDown={(event) => {
            if (disabled) {
              event.preventDefault();
              return;
            }

            if (event.key === "Enter" || event.key === " ") {
              if (!onUploadTrigger()) {
                event.preventDefault();
                return;
              }
              const input = document.getElementById(fileInputId) as HTMLInputElement | null;
              input?.click();
              event.preventDefault();
            }
          }}
        >
          +
        </label>
        <input
          id={fileInputId}
          className="composer-file-input visually-hidden-input"
          type="file"
          accept=".docx,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
          disabled={disabled}
          onChange={(event) => {
            const input = event.currentTarget;
            onFileSelect(input.files?.[0] ?? null);
            input.value = "";
          }}
        />

        {phase === "exporting" ? (
          <div className="composer-progress">
            <WaveExportProgress progress={exportProgress} />
          </div>
        ) : selectedFile ? (
          <div className="composer-file-pill" aria-label="当前已选文件">
            <strong>{selectedFile.name}</strong>
          </div>
        ) : (
          <textarea
            ref={textareaRef}
            className="composer-textarea"
            aria-label="论文正文输入框"
            placeholder={placeholder}
            value={rawText}
            disabled={disabled}
            onChange={(event) => onTextChange(event.target.value)}
            onKeyDown={(event) => {
              if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
                event.preventDefault();
                onSubmit();
              }
            }}
          />
        )}

        <button type="button" className="composer-submit" aria-label="开始预检" onClick={onSubmit} disabled={disabled}>
          →
        </button>
      </div>

      <div className="composer-meta">
        <p>{phase === "prechecking" ? "正在进行结构识别与规则检查…" : "按 Cmd/Ctrl + Enter 开始预检"}</p>
        {hasContent ? (
          <button type="button" className="composer-clear" onClick={onClear}>
            清空
          </button>
        ) : (
          <span className="composer-clear-placeholder" />
        )}
      </div>
    </div>
  );
}
