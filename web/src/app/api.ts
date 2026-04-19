import type { HealthResponse, NormalizedThesis, PrecheckResponse } from "../generated/contracts";

const importMetaEnv = (import.meta as ImportMeta & { env?: Record<string, string | undefined> }).env;
const API_BASE = (importMetaEnv?.VITE_API_BASE_URL ?? "").replace(/\/$/, "");
const STORY2PAPER_BASE = importMetaEnv?.VITE_STORY2PAPER_URL ?? "http://localhost:8000";

export type ApiErrorPayload = {
  error_code?: string;
  error_message?: string;
  details?: unknown;
};

export class ApiError extends Error {
  code?: string;
  details?: unknown;

  constructor(message: string, code?: string, details?: unknown) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.details = details;
  }
}

async function readError(response: Response): Promise<ApiError> {
  try {
    const payload = (await response.json()) as ApiErrorPayload;
    return new ApiError(payload.error_message || response.statusText, payload.error_code, payload.details);
  } catch {
    return new ApiError(response.statusText || "请求失败", "NETWORK_ERROR");
  }
}

async function jsonRequest<T>(input: RequestInfo | URL, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(buildApiUrl(input), init);
  } catch (error) {
    throw new ApiError(error instanceof Error ? error.message : "服务暂时不可用", "NETWORK_ERROR");
  }

  if (!response.ok) {
    throw await readError(response);
  }

  return (await response.json()) as T;
}

async function blobRequest(input: RequestInfo | URL, init?: RequestInit): Promise<Blob> {
  let response: Response;
  try {
    response = await fetch(buildApiUrl(input), init);
  } catch (error) {
    throw new ApiError(error instanceof Error ? error.message : "服务暂时不可用", "NETWORK_ERROR");
  }

  if (!response.ok) {
    throw await readError(response);
  }

  return response.blob();
}

function buildApiUrl(input: RequestInfo | URL): RequestInfo | URL {
  if (!API_BASE || typeof input !== "string" || !input.startsWith("/")) return input;
  return `${API_BASE}${input}`;
}

export function getHealth() {
  return jsonRequest<HealthResponse>("/api/health");
}

export function precheckDocx(file: File) {
  return publicPrecheckDocx(file, true, "");
}

export function publicPrecheckDocx(file: File, privacyAccepted: boolean, turnstileToken = "") {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("privacy_accepted", String(privacyAccepted));
  formData.append("turnstile_token", turnstileToken);
  return jsonRequest<PrecheckResponse>("/api/public/precheck/docx", {
    method: "POST",
    body: formData,
  });
}

export function precheckText(text: string) {
  return publicPrecheckText(text, true, "");
}

export function publicPrecheckText(text: string, privacyAccepted: boolean, turnstileToken = "") {
  return jsonRequest<PrecheckResponse>("/api/public/precheck/text", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, privacy_accepted: privacyAccepted, turnstile_token: turnstileToken }),
  });
}

export function exportDocx(thesis: NormalizedThesis) {
  return blobRequest("/api/export/docx", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(thesis),
  });
}

export interface PublicExportResponse {
  export_id: string;
  download_url: string;
  report_url: string;
  expires_at: string;
}

export function publicExportDocx(thesis: NormalizedThesis, exportToken: string) {
  return jsonRequest<PublicExportResponse>("/api/public/exports/docx", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ thesis, export_token: exportToken }),
  });
}

export function downloadUrlAsBlob(url: string) {
  return blobRequest(url);
}

export function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

// ─── Story2Paper Integration ─────────────────────────────────────────────────

export interface Story2PaperGenerateResponse {
  paper_id: string;
  status: string;
}

export interface Story2PaperResult {
  paper_id: string;
  outline: Record<string, unknown> | null;
  section_drafts: Array<{
    section_id: string;
    title: string;
    content: string;
  }>;
  contract: Record<string, unknown> | null;
  final_output: string | null;
  status: string;
}

export interface Story2PaperWSEvent {
  event: string;
  current_agent?: string;
  section_index?: number;
  audit_pass?: boolean;
  revision_round?: number;
  final_output?: boolean;
}

export async function story2paperGenerate(researchPrompt: string): Promise<Story2PaperGenerateResponse> {
  const response = await fetch(`${STORY2PAPER_BASE}/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ research_prompt: researchPrompt }),
  });
  if (!response.ok) {
    const text = await response.text();
    throw new ApiError(`Story2Paper 生成失败: ${response.status} ${text}`, "STORY2PAPER_ERROR");
  }
  return response.json() as Promise<Story2PaperGenerateResponse>;
}

export async function story2paperGetResult(paperId: string): Promise<Story2PaperResult> {
  const response = await fetch(`${STORY2PAPER_BASE}/generate/result/${paperId}`);
  if (!response.ok) {
    const text = await response.text();
    throw new ApiError(`获取生成结果失败: ${response.status} ${text}`, "STORY2PAPER_ERROR");
  }
  return response.json() as Promise<Story2PaperResult>;
}

export function story2paperWS(paperId: string): WebSocket {
  const wsUrl = STORY2PAPER_BASE.replace(/^http/, "ws") + `/ws/${paperId}`;
  return new WebSocket(wsUrl);
}

export function precheckFromStory2Paper(schemaData: object, cover: import("../generated/contracts").CoverFields) {
  return jsonRequest<PrecheckResponse>("/api/precheck/from-story2paper", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ schema_data: schemaData, cover }),
  });
}

// ─── Workbench API ───────────────────────────────────────────────────────────

export interface ThesisProject {
  id: string;
  title: string;
  school: string;
  degree_level: string;
  template_profile: string;
  rule_set_id: string;
  department: string;
  major: string;
  advisor: string;
  student_name: string;
  student_id: string;
  writing_stage: string;
  privacy_mode: string;
  remote_provider_allowed: boolean;
  status: string;
  current_version_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface ProjectDraft {
  title: string;
  department?: string;
  major?: string;
  advisor?: string;
  student_name?: string;
  student_id?: string;
  writing_stage?: string;
  privacy_mode?: string;
  remote_provider_allowed?: boolean;
}

export interface ProjectFileRecord {
  id: string;
  project_id: string;
  type: string;
  filename: string;
  content_type: string;
  size: number;
  sha256: string;
  storage_key: string;
  parser: string;
  source_label: string;
  created_at: string;
}

export interface WorkbenchJob {
  id: string;
  project_id: string | null;
  kind: string;
  status: string;
  current_agent: string | null;
  result: Record<string, unknown>;
}

export interface ThesisVersionRecord {
  id: string;
  project_id: string;
  parent_version_id: string | null;
  label: string;
  thesis: NormalizedThesis;
  created_by: string;
  created_at: string;
}

export interface ProposalRecord {
  id: string;
  project_id: string;
  version_id: string | null;
  target_block_id: string | null;
  operation: string;
  before: string;
  after: string;
  reason: string;
  risk: string;
  source_refs: unknown[];
  affects_export: boolean;
  status: string;
  created_at: string;
}

export interface ExportRecord {
  id: string;
  project_id: string;
  version_id: string;
  format: string;
  status: string;
  storage_key: string | null;
  filename: string;
  summary: Record<string, unknown>;
  created_at: string;
}

export interface ProviderOption {
  id: string;
  name: string;
  remote: boolean;
}

export interface ProviderConfigRecord {
  id: string;
  provider: string;
  model: string;
  base_url: string | null;
  allow_local: boolean;
  has_api_key: boolean;
  verification_status: string;
  verification_message: string;
  last_verified_at: string | null;
  created_at: string;
  updated_at: string;
}

export function createProject(input: string | ProjectDraft) {
  const payload = typeof input === "string" ? { title: input } : input;
  return jsonRequest<ThesisProject>("/api/projects", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function listProjects() {
  return jsonRequest<ThesisProject[]>("/api/projects");
}

export function updateProject(projectId: string, patch: Partial<ProjectDraft>) {
  return jsonRequest<ThesisProject>(`/api/projects/${projectId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(patch),
  });
}

export function uploadProjectFile(projectId: string, file: File, fileType = "docx") {
  const form = new FormData();
  form.append("file", file);
  form.append("file_type", fileType);
  form.append("source_label", "用户上传");
  return jsonRequest<ProjectFileRecord>(`/api/projects/${projectId}/files`, {
    method: "POST",
    body: form,
  });
}

export function listProjectFiles(projectId: string) {
  return jsonRequest<ProjectFileRecord[]>(`/api/projects/${projectId}/files`);
}

export function createParseJob(projectId: string, fileId: string) {
  return jsonRequest<WorkbenchJob>(`/api/projects/${projectId}/parse-jobs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ file_id: fileId }),
  });
}

export function getJobEvents(jobId: string) {
  return jsonRequest<Array<{ id: string; type: string; payload: Record<string, unknown>; created_at: string }>>(`/api/jobs/${jobId}/events`);
}

export function listVersions(projectId: string) {
  return jsonRequest<ThesisVersionRecord[]>(`/api/projects/${projectId}/versions`);
}

export function listProposals(projectId: string) {
  return jsonRequest<ProposalRecord[]>(`/api/projects/${projectId}/proposals`);
}

export function decideProposal(proposalId: string, decision: "accept" | "reject" | "stash") {
  return jsonRequest<{ proposal_id: string; decision: string; resulting_version_id: string | null }>(`/api/proposals/${proposalId}/${decision}`, {
    method: "POST",
  });
}

export function createProjectExport(projectId: string, format: "docx" | "pdf" | "markdown" | "integrity_report") {
  return jsonRequest<ExportRecord>(`/api/projects/${projectId}/exports`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ format }),
  });
}

export function listProjectExports(projectId: string) {
  return jsonRequest<ExportRecord[]>(`/api/projects/${projectId}/exports`);
}

export function getProviders() {
  return jsonRequest<{ providers: ProviderOption[]; keys_exposed: boolean; secret_storage: string }>("/api/providers");
}

export function listProviderConfigs() {
  return jsonRequest<ProviderConfigRecord[]>("/api/provider-configs");
}

export function saveProviderConfig(payload: { provider: string; model: string; base_url?: string; api_key?: string; allow_local?: boolean }) {
  return jsonRequest<ProviderConfigRecord>("/api/provider-configs", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function verifyProviderConfig(configId: string) {
  return jsonRequest<ProviderConfigRecord>(`/api/provider-configs/${configId}/verify`, {
    method: "POST",
  });
}

export function deleteProviderConfig(configId: string) {
  return jsonRequest<ProviderConfigRecord>(`/api/provider-configs/${configId}`, {
    method: "DELETE",
  });
}

export function getAccessCodeStatus() {
  return jsonRequest<{ required: boolean; verified: boolean }>("/api/access-code/status");
}

export function verifyAccessCode(accessCode: string) {
  return jsonRequest<{ required: boolean; verified: boolean }>("/api/access-code/verify", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ access_code: accessCode }),
  });
}

export function exportDownloadUrl(exportId: string) {
  const path = `/api/exports/${exportId}/download`;
  return typeof buildApiUrl(path) === "string" ? (buildApiUrl(path) as string) : path;
}
