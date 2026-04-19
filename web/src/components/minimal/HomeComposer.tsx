import { useEffect, useLayoutEffect, useRef, useState, type DragEvent as ReactDragEvent } from "react";
import type { FlowPhase } from "../../app/domain";
import { SegmentedControl } from "../ui/SegmentedControl";
import { WaveExportProgress } from "./WaveExportProgress";

type HomeComposerProps = {
  rawText: string;
  selectedFile: File | null;
  phase: FlowPhase;
  exportProgress: number;
  privacyAccepted: boolean;
  turnstileToken: string;
  onTextChange: (value: string) => void;
  onUploadTrigger: () => boolean;
  onFileSelect: (file: File | null) => void;
  onSubmit: () => void;
  onClear: () => void;
  onDragActiveChange?: (active: boolean) => void;
  onPrivacyAcceptedChange: (value: boolean) => void;
  onTurnstileTokenChange: (value: string) => void;
};

type TurnstileApi = {
  render: (container: HTMLElement, options: Record<string, unknown>) => string;
  reset: (id?: string) => void;
  remove: (id?: string) => void;
};

declare global {
  interface Window {
    turnstile?: TurnstileApi;
  }
}

const importMetaEnv = (import.meta as ImportMeta & { env?: Record<string, string | undefined> }).env;
const TURNSTILE_SITE_KEY = importMetaEnv?.VITE_TURNSTILE_SITE_KEY ?? "";

function hasFiles(event: Pick<DragEvent, "dataTransfer"> | Pick<ReactDragEvent, "dataTransfer">) {
  return Array.from(event.dataTransfer?.types ?? []).includes("Files");
}

export function HomeComposer({
  rawText,
  selectedFile,
  phase,
  exportProgress,
  privacyAccepted,
  turnstileToken,
  onTextChange,
  onUploadTrigger,
  onFileSelect,
  onSubmit,
  onClear,
  onDragActiveChange,
  onPrivacyAcceptedChange,
  onTurnstileTokenChange,
}: HomeComposerProps) {
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const turnstileRef = useRef<HTMLDivElement | null>(null);
  const turnstileWidgetIdRef = useRef<string | null>(null);
  const dragDepthRef = useRef(0);
  const [isDragActive, setIsDragActive] = useState(false);
  const hasContent = Boolean(selectedFile || rawText.trim());
  const disabled = phase === "prechecking" || phase === "exporting";
  const hintText =
    phase === "prechecking"
      ? "正在进行结构识别与规则检查…"
      : hasContent
        ? "按 Cmd/Ctrl + Enter 开始预检"
        : null;

  function setDragActive(active: boolean) {
    setIsDragActive(active);
    onDragActiveChange?.(active);
  }

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

  useEffect(() => {
    if (!TURNSTILE_SITE_KEY || !turnstileRef.current) return;

    function renderWidget() {
      if (!window.turnstile || !turnstileRef.current || turnstileWidgetIdRef.current) return;
      turnstileWidgetIdRef.current = window.turnstile.render(turnstileRef.current, {
        sitekey: TURNSTILE_SITE_KEY,
        callback: (token: string) => onTurnstileTokenChange(token),
        "expired-callback": () => onTurnstileTokenChange(""),
        "error-callback": () => onTurnstileTokenChange(""),
      });
    }

    if (!window.turnstile) {
      const existing = document.querySelector<HTMLScriptElement>('script[src="https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit"]');
      const script = existing ?? document.createElement("script");
      script.src = "https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit";
      script.async = true;
      script.defer = true;
      script.onload = renderWidget;
      if (!existing) document.head.appendChild(script);
    } else {
      renderWidget();
    }

    return () => {
      if (turnstileWidgetIdRef.current && window.turnstile) {
        window.turnstile.remove(turnstileWidgetIdRef.current);
        turnstileWidgetIdRef.current = null;
      }
    };
  }, [onTurnstileTokenChange]);

  function resetDragState() {
    dragDepthRef.current = 0;
    setDragActive(false);
  }

  return (
    <div className="composer-shell" data-has-content={hasContent} data-busy={disabled}>
      <div className="composer-tab-bar">
        <SegmentedControl
          label="输入来源"
          value="upload"
          onChange={() => undefined}
          options={[{ value: "upload", label: "快速导出" }]}
        />
      </div>

      <div
        className={`composer ${selectedFile ? "composer-file" : ""} ${disabled ? "composer-busy" : ""}`}
        data-drag-active={isDragActive}
        data-has-file={Boolean(selectedFile)}
        data-busy={disabled}
        tabIndex={selectedFile ? 0 : -1}
        aria-busy={disabled}
        onKeyDown={(event) => {
          if (!selectedFile || disabled) return;
          if (event.key === "Enter") {
            event.preventDefault();
            onSubmit();
          }
        }}
        onDragEnter={(event) => {
          if (!hasFiles(event)) return;
          event.preventDefault();
          dragDepthRef.current += 1;
          if (!disabled) setDragActive(true);
        }}
        onDragOver={(event) => {
          if (!hasFiles(event)) return;
          event.preventDefault();
          event.dataTransfer.dropEffect = disabled ? "none" : "copy";
          if (!disabled && !isDragActive) setDragActive(true);
        }}
        onDragLeave={(event) => {
          if (!hasFiles(event)) return;
          event.preventDefault();
          dragDepthRef.current = Math.max(0, dragDepthRef.current - 1);
          if (dragDepthRef.current === 0) setDragActive(false);
        }}
        onDrop={(event) => {
          if (!hasFiles(event)) return;
          event.preventDefault();
          const file = event.dataTransfer.files?.[0] ?? null;
          resetDragState();
          if (!file || disabled) return;
          if (!onUploadTrigger()) return;
          onFileSelect(file);
        }}
      >
        <button
          type="button"
          className="composer-plus"
          aria-label="上传 .docx 文件"
          disabled={disabled}
          onClick={() => {
            if (!onUploadTrigger()) return;
            fileInputRef.current?.click();
          }}
        >
          +
        </button>
        <input
          ref={fileInputRef}
          className="composer-file-input visually-hidden-input"
          type="file"
          accept=".docx,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
          hidden
          tabIndex={-1}
          aria-hidden="true"
          disabled={disabled}
          onFocus={(event) => {
            event.currentTarget.blur();
          }}
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
            placeholder="粘贴已有论文正文进行格式预检"
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

        <button
          type="button"
          className="composer-submit"
          aria-label="开始预检"
          onClick={onSubmit}
          disabled={disabled}
        >
          →
        </button>
      </div>

      <label className="privacy-confirm">
        <input
          type="checkbox"
          checked={privacyAccepted}
          disabled={disabled}
          onChange={(event) => onPrivacyAcceptedChange(event.currentTarget.checked)}
        />
        <span>我确认已阅读隐私说明：公开站仅处理已有论文材料，导出文件保留 30 分钟，不启用远程 AI。</span>
      </label>

      {TURNSTILE_SITE_KEY ? (
        <div className="turnstile-box" ref={turnstileRef} aria-label="人机验证" data-ready={Boolean(turnstileToken)} />
      ) : (
        <p className="turnstile-note">生产环境将启用 Cloudflare Turnstile；本地开发不需要人机验证。</p>
      )}

      <div className="composer-meta">
        <div className="composer-hint-shell" aria-live="polite">
          {hintText ? (
            <p className="composer-hint">{hintText}</p>
          ) : (
            <span className="composer-hint-placeholder" aria-hidden="true" />
          )}
        </div>
        {hasContent ? (
          <button type="button" className="composer-clear" onClick={onClear} disabled={disabled}>
            清空
          </button>
        ) : (
          <span className="composer-clear-placeholder" />
        )}
      </div>
    </div>
  );
}
