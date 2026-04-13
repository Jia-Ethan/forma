import type { NormalizedThesis, PrecheckIssue } from "../generated/contracts";
import { ApiError } from "./api";

export type FlowPhase = "idle" | "text_ready" | "file_ready" | "prechecking" | "preview_modal_open" | "exporting";

export type InlineErrorState = {
  message: string;
  code?: string;
};

export function inferPhase(rawText: string, selectedFile: File | null, busy: boolean, modalOpen: boolean, exporting: boolean): FlowPhase {
  if (exporting) return "exporting";
  if (modalOpen) return "preview_modal_open";
  if (busy) return "prechecking";
  if (selectedFile) return "file_ready";
  if (rawText.trim()) return "text_ready";
  return "idle";
}

export function validateDocxFile(file: File | null): InlineErrorState | null {
  if (!file) return { message: "请先选择一个 `.docx` 文件。", code: "UNSUPPORTED_FILE_TYPE" };
  if (!file.name.toLowerCase().endsWith(".docx")) {
    return { message: "当前仅支持上传 `.docx` 文件。", code: "UNSUPPORTED_FILE_TYPE" };
  }
  return null;
}

export function validateTextInput(rawText: string): InlineErrorState | null {
  if (!rawText.trim()) {
    return { message: "内容为空，无法开始处理。", code: "CONTENT_EMPTY" };
  }
  return null;
}

export function mapApiError(error: ApiError | null): InlineErrorState | null {
  if (!error) return null;
  const map: Record<string, string> = {
    UNSUPPORTED_FILE_TYPE: "当前仅支持上传 `.docx` 文件。",
    CONTENT_EMPTY: "内容为空，无法开始处理。",
    DOCX_INVALID: "上传文件不是有效的 `.docx` 文档。",
    FILE_TOO_LARGE: "文件超过当前上传大小限制，请压缩后再试。",
    PARSE_FAILED: "无法完成结构识别，请调整输入内容后重试。",
    FIELD_MISSING: "预检仍有阻塞项，暂时无法导出。",
    TEMPLATE_DEPENDENCY_MISSING: "导出模板当前不可用，请稍后重试。",
    EXPORT_FAILED: "导出失败，请稍后重试。",
    NETWORK_ERROR: "服务暂时不可用，请稍后重试。",
  };

  return {
    message: map[error.code || ""] ?? error.message,
    code: error.code,
  };
}

export function issueText(issue: PrecheckIssue) {
  return `${issue.title}：${issue.message}`;
}

export function issueCount(issues: PrecheckIssue[], severity: "blocking" | "warning" | "info") {
  return issues.filter((item) => item.severity === severity).length;
}

export function exportFilename(thesis: NormalizedThesis) {
  const raw = thesis.metadata.title.trim() || "SC-TH-export";
  const safe = raw.replace(/[\\/:*?"<>|]/g, "-").slice(0, 80);
  return `${safe || "SC-TH-export"}.docx`;
}
