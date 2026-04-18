import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { WorkbenchApp } from "./WorkbenchApp";
import type { ProviderConfigRecord, ThesisProject } from "../app/api";
import { jsonResponse } from "../test/fixtures";

function project(overrides: Partial<ThesisProject> = {}): ThesisProject {
  return {
    id: "proj_1",
    title: "测试论文",
    school: "scnu",
    degree_level: "undergraduate",
    template_profile: "scnu-undergraduate",
    rule_set_id: "scnu-undergraduate-2025",
    department: "软件学院",
    major: "软件工程",
    advisor: "李老师",
    student_name: "张三",
    student_id: "2020123456",
    writing_stage: "draft",
    privacy_mode: "local_only",
    remote_provider_allowed: false,
    status: "active",
    current_version_id: null,
    created_at: "2026-04-18T00:00:00",
    updated_at: "2026-04-18T00:00:00",
    ...overrides,
  };
}

function providerConfig(overrides: Partial<ProviderConfigRecord> = {}): ProviderConfigRecord {
  return {
    id: "prov_1",
    provider: "openai",
    model: "gpt-test",
    base_url: null,
    allow_local: false,
    has_api_key: true,
    verification_status: "untested",
    verification_message: "",
    last_verified_at: null,
    created_at: "2026-04-18T00:00:00",
    updated_at: "2026-04-18T00:00:00",
    ...overrides,
  };
}

function mockWorkbenchFetch(options: { projects?: ThesisProject[]; configs?: ProviderConfigRecord[]; accessRequired?: boolean } = {}) {
  let projects = options.projects ?? [];
  let configs = options.configs ?? [];
  let accessVerified = !options.accessRequired;
  const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    const method = init?.method ?? "GET";
    if (url.endsWith("/api/access-code/status")) return jsonResponse({ required: !!options.accessRequired, verified: accessVerified });
    if (url.endsWith("/api/access-code/verify")) {
      accessVerified = true;
      return jsonResponse({ required: true, verified: true });
    }
    if (url.endsWith("/api/projects") && method === "GET") return jsonResponse(projects);
    if (url.endsWith("/api/projects") && method === "POST") {
      const body = JSON.parse(String(init?.body || "{}"));
      const created = project({ ...body, id: "proj_created", title: body.title || "未命名论文项目" });
      projects = [created, ...projects];
      return jsonResponse(created);
    }
    if (url.includes("/api/projects/proj_1") && method === "PATCH") {
      const body = JSON.parse(String(init?.body || "{}"));
      projects = projects.map((item) => (item.id === "proj_1" ? { ...item, ...body } : item));
      return jsonResponse(projects[0]);
    }
    if (url.endsWith("/api/providers")) {
      return jsonResponse({
        providers: [
          { id: "ollama", name: "Ollama", remote: false },
          { id: "openai", name: "OpenAI", remote: true },
        ],
        keys_exposed: false,
        secret_storage: "insecure-local-dev",
      });
    }
    if (url.endsWith("/api/provider-configs") && method === "GET") return jsonResponse(configs);
    if (url.endsWith("/api/provider-configs") && method === "POST") {
      const body = JSON.parse(String(init?.body || "{}"));
      configs = [providerConfig({ provider: body.provider, model: body.model, base_url: body.base_url ?? null })];
      return jsonResponse(configs[0]);
    }
    if (url.includes("/files") || url.includes("/versions") || url.includes("/proposals") || url.includes("/exports")) return jsonResponse([]);
    return jsonResponse({});
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

describe("WorkbenchApp", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("shows the empty state and creates a project from the wizard", async () => {
    const fetchMock = mockWorkbenchFetch();
    render(<WorkbenchApp />);

    expect(await screen.findByText("先建立一个可追溯的论文项目")).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("论文题目"), { target: { value: "阶段一论文" } });
    fireEvent.click(screen.getByRole("button", { name: "创建项目" }));

    await screen.findByText("项目已创建，可以上传论文材料。");
    const createCall = fetchMock.mock.calls.find(([input, init]) => String(input).endsWith("/api/projects") && init?.method === "POST");
    expect(createCall).toBeTruthy();
    const body = JSON.parse(String((createCall?.[1] as RequestInit).body));
    expect(body.privacy_mode).toBe("local_only");
    expect(body.remote_provider_allowed).toBe(false);
  });

  it("updates privacy consent before remote model use", async () => {
    mockWorkbenchFetch({ projects: [project()] });
    render(<WorkbenchApp />);

    expect(await screen.findByText("本地优先模式")).toBeInTheDocument();
    fireEvent.click(screen.getByLabelText("允许远程 Provider"));
    fireEvent.click(screen.getByLabelText("确认远程处理提示"));
    fireEvent.click(screen.getByRole("button", { name: "保存项目设置" }));

    expect(await screen.findByText("远程模型已授权")).toBeInTheDocument();
  });

  it("saves provider settings without rendering the raw API key", async () => {
    mockWorkbenchFetch({ projects: [project({ privacy_mode: "remote_allowed", remote_provider_allowed: true })] });
    render(<WorkbenchApp />);

    await screen.findByText("Provider 设置");
    fireEvent.change(screen.getByLabelText("Provider"), { target: { value: "openai" } });
    fireEvent.change(screen.getByLabelText("模型"), { target: { value: "gpt-test" } });
    fireEvent.change(screen.getByLabelText("API key"), { target: { value: "super-secret" } });
    fireEvent.click(screen.getByRole("button", { name: "保存 Provider" }));

    expect(await screen.findByText(/已保存 API key/)).toBeInTheDocument();
    expect(screen.queryByText("super-secret")).not.toBeInTheDocument();
  });

  it("blocks the workbench behind the access code gate", async () => {
    mockWorkbenchFetch({ accessRequired: true });
    render(<WorkbenchApp />);

    expect(await screen.findByText("该部署已启用访问码保护。验证后再进入项目、文件和 Provider 设置。")).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("访问码"), { target: { value: "phase-one" } });
    fireEvent.click(screen.getByRole("button", { name: "进入 Workbench" }));

    await waitFor(() => expect(screen.queryByText("该部署已启用访问码保护。验证后再进入项目、文件和 Provider 设置。")).not.toBeInTheDocument());
    expect(await screen.findByText("先建立一个可追溯的论文项目")).toBeInTheDocument();
  });
});
