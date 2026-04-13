import { useMemo, useRef } from "react";
import type { FlowPhase } from "../../app/domain";
import { WaveExportProgress } from "./WaveExportProgress";

type HomeComposerProps = {
  rawText: string;
  selectedFile: File | null;
  phase: FlowPhase;
  exportProgress: number;
  onTextChange: (value: string) => void;
  onFileSelect: (file: File | null) => void;
  onSubmit: () => void;
  onClear: () => void;
};

export function HomeComposer({ rawText, selectedFile, phase, exportProgress, onTextChange, onFileSelect, onSubmit, onClear }: HomeComposerProps) {
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const hasContent = Boolean(selectedFile || rawText.trim());
  const disabled = phase === "prechecking" || phase === "exporting";

  const placeholder = useMemo(() => {
    if (selectedFile) return selectedFile.name;
    return "上传 .docx 或粘贴论文内容，然后开始预检";
  }, [selectedFile]);

  return (
    <div className="composer-shell">
      <div className={`composer ${selectedFile ? "composer-file" : ""} ${disabled ? "composer-busy" : ""}`} tabIndex={selectedFile ? 0 : -1} onKeyDown={(event) => {
        if (!selectedFile || disabled) return;
        if (event.key === "Enter") {
          event.preventDefault();
          onSubmit();
        }
      }}>
        <button
          type="button"
          className="composer-plus"
          aria-label="上传 .docx 文件"
          onClick={() => fileInputRef.current?.click()}
          disabled={disabled}
        >
          +
        </button>
        <input
          ref={fileInputRef}
          className="composer-file-input"
          type="file"
          accept=".docx,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
          onChange={(event) => onFileSelect(event.target.files?.[0] ?? null)}
        />

        {phase === "exporting" ? (
          <div className="composer-progress">
            <WaveExportProgress progress={exportProgress} />
          </div>
        ) : selectedFile ? (
          <div className="composer-file-pill" aria-label="当前已选文件">
            <strong>{selectedFile.name}</strong>
            <span>按回车或点击右侧按钮开始预检</span>
          </div>
        ) : (
          <textarea
            className="composer-textarea"
            aria-label="论文正文输入框"
            rows={Math.min(Math.max(rawText.split("\n").length || 1, 1), 10)}
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
        <p>{phase === "prechecking" ? "正在进行结构识别与规则检查…" : "文本模式下按 Cmd/Ctrl + Enter 开始预检。"}</p>
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
