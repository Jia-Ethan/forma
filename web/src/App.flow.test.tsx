import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { App } from "./App";
import { healthPayload, jsonResponse, samplePrecheck, sampleThesis } from "./test/fixtures";

function mockFetch(handler: (input: RequestInfo | URL, init?: RequestInit) => Promise<Response>) {
  const fetchMock = vi.fn((input: RequestInfo | URL, init?: RequestInit) => handler(input, init));
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

function deferredResponse() {
  let resolve!: (value: Response) => void;
  const promise = new Promise<Response>((resolver) => {
    resolve = resolver;
  });
  return { promise, resolve };
}

describe("App business flow", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  function acceptPrivacy() {
    fireEvent.click(screen.getByRole("checkbox", { name: /我确认已阅读隐私说明/ }));
  }

  it("shows a backend precheck error below the composer", async () => {
    mockFetch((input) => {
      const url = String(input);
      if (url.includes("/api/public/precheck/text")) {
        return jsonResponse({ error_code: "PARSE_FAILED", error_message: "解析失败" }, false);
      }
      return jsonResponse(healthPayload);
    });

    render(<App />);
    fireEvent.change(screen.getByLabelText("论文正文输入框"), {
      target: { value: "不完整内容" },
    });
    acceptPrivacy();
    fireEvent.click(screen.getByRole("button", { name: "开始预检" }));

    expect(await screen.findByText("无法完成结构识别，请调整输入内容后重试。")).toBeInTheDocument();
  });

  it("keeps confirm button disabled when blocking issues remain", async () => {
    mockFetch((input) => {
      const url = String(input);
      if (url.includes("/api/public/precheck/text")) {
        return jsonResponse(
          samplePrecheck({
            summary: {
              can_confirm: false,
              blocking_count: 2,
              warning_count: 1,
              info_count: 2,
              blocking_message: "当前仍有 2 项阻塞问题，暂时无法导出。",
              warning_message: "另有 1 项警告，其中缺失章节会按留白位保留，复杂元素需人工复核。",
            },
            issues: [
              {
                id: "body-missing",
                code: "BODY_MISSING",
                severity: "blocking",
                block: "body",
                title: "正文主体不足",
                message: "未识别到足够的正文内容，当前无法生成可用的论文主文。",
                block_id: null,
                source_span: null,
                rule_source_id: null,
                suggested_action: null,
              },
            ],
            preview_blocks: samplePrecheck().preview_blocks.map((block) =>
              block.key === "body" ? { ...block, status: "blocking", preview: "正文内容不足", issue_ids: ["body-missing"] } : block,
            ),
          }),
        );
      }
      return jsonResponse(healthPayload);
    });

    render(<App />);
    fireEvent.change(screen.getByLabelText("论文正文输入框"), {
      target: { value: "摘要\n内容不足" },
    });
    acceptPrivacy();
    fireEvent.click(screen.getByRole("button", { name: "开始预检" }));

    expect(await screen.findByRole("button", { name: "仍有 2 项未满足" })).toBeDisabled();
  });

  it("exports docx and resets after success", async () => {
    const fetchMock = mockFetch((input, init) => {
      const url = String(input);
      if (url.includes("/api/public/precheck/text")) {
        return jsonResponse(samplePrecheck({ thesis: sampleThesis() }));
      }
      if (url.includes("/api/public/exports/docx")) {
        return jsonResponse({ export_id: "pub_1", download_url: "/api/public/exports/pub_1/download", report_url: "/api/public/exports/pub_1/report", expires_at: "2099-01-01T00:00:00" });
      }
      if (url.includes("/api/public/exports/pub_1/download")) {
        return jsonResponse({});
      }
      return jsonResponse(healthPayload);
    });

    Object.defineProperty(URL, "createObjectURL", { value: vi.fn(() => "blob:docx"), configurable: true });
    Object.defineProperty(URL, "revokeObjectURL", { value: vi.fn(), configurable: true });
    vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => undefined);

    render(<App />);

    fireEvent.change(screen.getByLabelText("论文正文输入框"), {
      target: { value: "结构化映射示例论文\n\n摘要\n这是满足长度要求的摘要内容。".repeat(8) },
    });
    acceptPrivacy();
    fireEvent.click(screen.getByRole("button", { name: "开始预检" }));
    await screen.findByRole("dialog", { name: "导出前结构预检" });

    fireEvent.click(screen.getByRole("button", { name: "确认并导出" }));

    expect(await screen.findByText("正在生成 Word 文件")).toBeInTheDocument();
    await waitFor(() => expect(screen.queryByRole("dialog", { name: "导出前结构预检" })).not.toBeInTheDocument());
    await waitFor(() => expect(screen.getByLabelText("论文正文输入框")).toHaveValue(""));

    const exportCall = fetchMock.mock.calls.find(([input]) => String(input).includes("/api/public/exports/docx"));
    expect(exportCall).toBeTruthy();
    const [, request] = exportCall as [RequestInfo | URL, RequestInit];
    const payload = JSON.parse(String(request.body));
    expect(payload.thesis.cover.title).toBe("结构化映射示例论文");
    expect(payload.export_token).toBe("v1:9999999999:test:signature");
  });

  it("keeps upload disabled while precheck is in flight", async () => {
    const precheckDeferred = deferredResponse();
    mockFetch((input) => {
      const url = String(input);
      if (url.includes("/api/public/precheck/text")) {
        return precheckDeferred.promise;
      }
      return jsonResponse(healthPayload);
    });

    const { container } = render(<App />);

    fireEvent.change(screen.getByLabelText("论文正文输入框"), {
      target: { value: "结构化映射示例论文\n\n摘要\n这是满足长度要求的摘要内容。".repeat(8) },
    });
    acceptPrivacy();
    fireEvent.click(screen.getByRole("button", { name: "开始预检" }));

    const uploadButton = screen.getByRole("button", { name: "上传 .docx 文件" });
    const input = container.querySelector('input[type="file"]') as HTMLInputElement;
    const clickSpy = vi.spyOn(input, "click");

    await waitFor(() => expect(uploadButton).toBeDisabled());
    fireEvent.click(uploadButton);
    expect(clickSpy).not.toHaveBeenCalled();

    precheckDeferred.resolve(await jsonResponse(samplePrecheck()));
    expect(await screen.findByRole("dialog", { name: "导出前结构预检" })).toBeInTheDocument();
  });

  it("keeps upload disabled while export is in flight", async () => {
    const exportDeferred = deferredResponse();
    mockFetch((input) => {
      const url = String(input);
      if (url.includes("/api/public/precheck/text")) {
        return jsonResponse(samplePrecheck({ thesis: sampleThesis() }));
      }
      if (url.includes("/api/public/exports/docx")) {
        return exportDeferred.promise;
      }
      if (url.includes("/api/public/exports/pub_1/download")) {
        return jsonResponse({});
      }
      return jsonResponse(healthPayload);
    });

    Object.defineProperty(URL, "createObjectURL", { value: vi.fn(() => "blob:docx"), configurable: true });
    Object.defineProperty(URL, "revokeObjectURL", { value: vi.fn(), configurable: true });
    vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => undefined);

    const { container } = render(<App />);
    fireEvent.change(screen.getByLabelText("论文正文输入框"), {
      target: { value: "结构化映射示例论文\n\n摘要\n这是满足长度要求的摘要内容。".repeat(8) },
    });
    acceptPrivacy();
    fireEvent.click(screen.getByRole("button", { name: "开始预检" }));
    await screen.findByRole("dialog", { name: "导出前结构预检" });
    fireEvent.click(screen.getByRole("button", { name: "确认并导出" }));

    const uploadButton = screen.getByRole("button", { name: "上传 .docx 文件" });
    const input = container.querySelector('input[type="file"]') as HTMLInputElement;
    const clickSpy = vi.spyOn(input, "click");

    await waitFor(() => expect(uploadButton).toBeDisabled());
    expect(await screen.findByText("正在生成 Word 文件")).toBeInTheDocument();
    fireEvent.click(uploadButton);
    expect(clickSpy).not.toHaveBeenCalled();

    exportDeferred.resolve(await jsonResponse({ export_id: "pub_1", download_url: "/api/public/exports/pub_1/download", report_url: "/api/public/exports/pub_1/report", expires_at: "2099-01-01T00:00:00" }));
    await waitFor(() => expect(screen.getByLabelText("论文正文输入框")).toHaveValue(""));
  });
});
