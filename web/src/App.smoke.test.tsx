import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { App } from "./App";
import { healthPayload, jsonResponse, samplePrecheck } from "./test/fixtures";

function mockFetch(handler?: (input: RequestInfo | URL, init?: RequestInit) => Promise<Response>) {
  const fetchMock = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
    if (handler) return handler(input, init);
    return jsonResponse(healthPayload);
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

describe("App smoke", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("renders the minimal home shell", async () => {
    mockFetch();

    render(<App />);

    expect(screen.getByText("SC-TH")).toBeInTheDocument();
    expect(screen.getByText("极简论文预检与 Word 导出")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "上传 .docx 文件" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "开始预检" })).toBeInTheDocument();

    await waitFor(() => expect(fetch).toHaveBeenCalledWith("/api/health", undefined));
  });

  it("shows inline guidance when trying to submit empty content", async () => {
    const fetchMock = mockFetch();

    render(<App />);

    fireEvent.click(screen.getByRole("button", { name: "开始预检" }));

    expect(await screen.findByText("内容为空，无法开始处理。")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("opens preview modal after text precheck succeeds", async () => {
    mockFetch((input) => {
      const url = String(input);
      if (url.includes("/api/precheck/text")) return jsonResponse(samplePrecheck());
      return jsonResponse(healthPayload);
    });

    render(<App />);

    fireEvent.change(screen.getByLabelText("论文正文输入框"), {
      target: { value: "结构化映射示例论文\n\n摘要\n本文展示结构化映射后的论文导出流程，并说明新的预检主线。\n\n引言\n这是足够长的正文内容，用于通过预检。".repeat(10) },
    });
    fireEvent.click(screen.getByRole("button", { name: "开始预检" }));

    expect(await screen.findByRole("dialog", { name: "导出前结构预检" })).toBeInTheDocument();
    expect(screen.getByText("预检已通过，可以开始导出 Word 文件。")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "确认并导出" })).toBeEnabled();
  });

  it("keeps input after canceling preview modal", async () => {
    mockFetch((input) => {
      const url = String(input);
      if (url.includes("/api/precheck/text")) return jsonResponse(samplePrecheck());
      return jsonResponse(healthPayload);
    });

    render(<App />);

    const textarea = screen.getByLabelText("论文正文输入框");
    fireEvent.change(textarea, {
      target: { value: "我的论文标题\n\n摘要\n这是摘要。" },
    });
    fireEvent.click(screen.getByRole("button", { name: "开始预检" }));

    await screen.findByRole("dialog", { name: "导出前结构预检" });
    fireEvent.click(screen.getByRole("button", { name: "取消" }));

    await waitFor(() => expect(screen.queryByRole("dialog", { name: "导出前结构预检" })).not.toBeInTheDocument());
    expect(screen.getByLabelText("论文正文输入框")).toHaveValue("我的论文标题\n\n摘要\n这是摘要。");
  });
});
