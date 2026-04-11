import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { App } from "./App";
import { healthPayload, jsonResponse, sampleThesis } from "./test/fixtures";

function mockFetch(handler: (input: RequestInfo | URL, init?: RequestInit) => Promise<Response>) {
  const fetchMock = vi.fn((input: RequestInfo | URL, init?: RequestInit) => handler(input, init));
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

async function parseTextSuccessfully() {
  fireEvent.click(screen.getByRole("tab", { name: /粘贴正文/ }));
  fireEvent.change(screen.getByLabelText("论文正文"), {
    target: { value: "# 引言\n\n这是正文。\n\n# 参考文献\n\n【1】示例作者. 论文模板实践." },
  });
  fireEvent.click(screen.getByRole("button", { name: "开始识别" }));
  await screen.findByText("封面字段");
}

describe("App business flow", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("shows a network error when health check cannot reach the service", async () => {
    mockFetch(() => Promise.reject(new Error("Failed to fetch")));

    render(<App />);

    expect(await screen.findByText("服务暂时不可用")).toBeInTheDocument();
    expect(screen.getByText("请确认本地后端或线上服务可访问后再试。")).toBeInTheDocument();
  });

  it("shows a friendly backend 4xx parse error", async () => {
    mockFetch((input) => {
      const url = String(input);
      if (url.includes("/api/normalize/text")) {
        return jsonResponse({ error_code: "PARSE_FAILED", error_message: "解析失败" }, false);
      }
      return jsonResponse(healthPayload);
    });

    render(<App />);
    await screen.findAllByText("latex-scnu-web");
    fireEvent.click(screen.getByRole("tab", { name: /粘贴正文/ }));
    fireEvent.change(screen.getByLabelText("论文正文"), {
      target: { value: "# 引言\n\n这是正文。" },
    });
    fireEvent.click(screen.getByRole("button", { name: "开始识别" }));

    expect(await screen.findByText("结构识别没有完成")).toBeInTheDocument();
    expect(screen.getByText("请先尝试粘贴正文；如果仍失败，保留原文后人工拆分章节。")).toBeInTheDocument();
  });

  it("shows a friendly backend 5xx export error", async () => {
    mockFetch((input) => {
      const url = String(input);
      if (url.includes("/api/normalize/text")) return jsonResponse(sampleThesis());
      if (url.includes("/api/export/texzip")) {
        return jsonResponse({ error_code: "EXPORT_FAILED", error_message: "导出 PDF 失败。" }, false, "Internal Server Error");
      }
      return jsonResponse(healthPayload);
    });

    render(<App />);
    await screen.findAllByText("latex-scnu-web");
    await parseTextSuccessfully();
    fireEvent.click(screen.getByRole("button", { name: "导出 .tex 工程 zip" }));

    expect(await screen.findByText("导出没有完成")).toBeInTheDocument();
    expect(screen.getByText("请检查字段内容是否完整，再重新导出 .tex 工程 zip。")).toBeInTheDocument();
  });

  it("parses, edits metadata, and exports tex zip with the latest payload", async () => {
    const fetchMock = mockFetch((input) => {
      const url = String(input);
      if (url.includes("/api/normalize/text")) return jsonResponse(sampleThesis());
      if (url.includes("/api/export/texzip")) return jsonResponse({});
      return jsonResponse(healthPayload);
    });
    Object.defineProperty(URL, "createObjectURL", { value: vi.fn(() => "blob:texzip"), configurable: true });
    Object.defineProperty(URL, "revokeObjectURL", { value: vi.fn(), configurable: true });
    vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => undefined);

    render(<App />);
    await screen.findAllByText("latex-scnu-web");
    await parseTextSuccessfully();
    fireEvent.change(screen.getByLabelText("论文题目"), { target: { value: "最终导出题目" } });
    fireEvent.click(screen.getByRole("button", { name: "导出 .tex 工程 zip" }));

    expect(await screen.findByText("可以下载后在本地继续调整与编译。")).toBeInTheDocument();

    const exportCall = fetchMock.mock.calls.find(([input]) => String(input).includes("/api/export/texzip"));
    expect(exportCall).toBeTruthy();
    const [, request] = exportCall as [RequestInfo | URL, RequestInit];
    const payload = JSON.parse(String(request.body));
    expect(payload.metadata.title).toBe("最终导出题目");
  });
});
