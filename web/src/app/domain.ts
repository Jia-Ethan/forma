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
  if (file.size > 20 * 1024 * 1024) {
    return { message: "文件超过 20 MB，请压缩或删减后再试。", code: "FILE_TOO_LARGE" };
  }
  return null;
}

export function validateTextInput(rawText: string): InlineErrorState | null {
  if (!rawText.trim()) {
    return { message: "内容为空，无法开始处理。", code: "CONTENT_EMPTY" };
  }
  if (rawText.length > 80_000) {
    return { message: "粘贴正文超过 80,000 字，请改为上传 `.docx`。", code: "TEXT_TOO_LONG" };
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
    TEXT_TOO_LONG: "粘贴正文超过 80,000 字，请改为上传 `.docx`。",
    PRIVACY_CONFIRMATION_REQUIRED: "请先确认隐私说明后再继续。",
    TURNSTILE_REQUIRED: "请完成人机验证后再提交。",
    TURNSTILE_INVALID: "人机验证未通过，请刷新后重试。",
    RATE_LIMITED: "当前 IP 的公开导出请求过于频繁，请稍后再试。",
    EXPORT_TOKEN_INVALID: "导出凭证已失效，请重新预检后再导出。",
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
  const raw = thesis.cover.title.trim() || "SC-TH-export";
  const safe = raw.replace(/[\\/:*?"<>|]/g, "-").slice(0, 80);
  return `${safe || "SC-TH-export"}.docx`;
}
