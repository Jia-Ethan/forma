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
    window.history.replaceState(null, "", "/");
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  function acceptPrivacy() {
    fireEvent.click(screen.getByRole("checkbox", { name: /我确认已阅读隐私说明/ }));
  }

  it("renders the minimal home shell", async () => {
    mockFetch();

    const { container } = render(<App />);

    expect(screen.getByRole("heading", { level: 1, name: "华师本科论文格式合规与版本工作台" })).toBeInTheDocument();
    expect(screen.getByText(/公开站只做快速格式预检与 Word 导出，不启用远程 AI/)).toBeInTheDocument();
    expect(screen.queryByText("极简论文预检与 Word 导出")).not.toBeInTheDocument();
    expect(screen.queryByPlaceholderText("上传 .docx 或粘贴论文内容")).not.toBeInTheDocument();
    expect(screen.queryByText("按 Cmd/Ctrl + Enter 开始预检")).not.toBeInTheDocument();
    const uploadButton = screen.getByRole("button", { name: "上传 .docx 文件" });
    const input = container.querySelector('input[type="file"]') as HTMLInputElement;
    expect(uploadButton.tagName).toBe("BUTTON");
    expect(uploadButton).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "开始预检" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "查看 Workbench" })).toHaveAttribute("href", "#/workbench-demo");
    expect(screen.getByRole("link", { name: "English" })).toHaveAttribute("href", "#/en");
    expect(screen.getByPlaceholderText("粘贴已有论文正文进行格式预检")).toBeInTheDocument();
    expect(screen.queryByText("生成论文")).not.toBeInTheDocument();
    expect(screen.queryByText("AI 生成")).not.toBeInTheDocument();
    expect(input.tabIndex).toBe(-1);
    expect(input).toHaveAttribute("aria-hidden", "true");

    await waitFor(() => expect(fetch).toHaveBeenCalledWith("/api/health", undefined));
  });

  it("shows inline guidance when trying to submit empty content", async () => {
    const fetchMock = mockFetch();

    render(<App />);

    fireEvent.click(screen.getByRole("button", { name: "开始预检" }));

    expect(await screen.findByText("内容为空，无法开始处理。")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("requires privacy confirmation before precheck", async () => {
    mockFetch();

    render(<App />);
    fireEvent.change(screen.getByLabelText("论文正文输入框"), {
      target: { value: "已有论文正文" },
    });
    fireEvent.click(screen.getByRole("button", { name: "开始预检" }));

    expect(await screen.findByText("请先确认隐私说明后再继续。")).toBeInTheDocument();
  });

  it("renders the public Workbench demo without booting private APIs", async () => {
    window.history.replaceState(null, "", "/#/workbench-demo");
    const fetchMock = mockFetch();

    render(<App />);

    expect(screen.getByRole("heading", { level: 1, name: "SCNU Thesis Agent Workbench Demo" })).toBeInTheDocument();
    expect(screen.getByText("安全示例项目，不包含真实论文正文，不调用远程 Provider。")).toBeInTheDocument();
    expect(screen.getAllByText("基于学习投入的本科论文示例")).toHaveLength(2);
    expect(screen.getByRole("button", { name: "重置 demo" })).toBeInTheDocument();
    fireEvent.click(screen.getAllByRole("button", { name: "接受" })[0]);
    expect(screen.getAllByText("accepted").length).toBeGreaterThan(1);
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("shows the selected docx filename after upload", async () => {
    mockFetch();
    const { container } = render(<App />);

    const uploadButton = screen.getByRole("button", { name: "上传 .docx 文件" });
    const input = container.querySelector('input[type="file"]') as HTMLInputElement;
    const clickSpy = vi.spyOn(input, "click");
    const file = new File(["docx"], "paper.docx", {
      type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    });

    fireEvent.click(uploadButton);
    expect(clickSpy).toHaveBeenCalledTimes(1);
    fireEvent.change(input, { target: { files: [file] } });

    expect(await screen.findByText("paper.docx")).toBeInTheDocument();
  });

  it("shows shortcut hint only when the composer has content", async () => {
    mockFetch();

    render(<App />);

    const textarea = screen.getByLabelText("论文正文输入框");
    expect(screen.queryByText("按 Cmd/Ctrl + Enter 开始预检")).not.toBeInTheDocument();

    fireEvent.change(textarea, { target: { value: "这是正文内容" } });
    expect(await screen.findByText("按 Cmd/Ctrl + Enter 开始预检")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "清空" }));
    await waitFor(() => expect(screen.queryByText("按 Cmd/Ctrl + Enter 开始预检")).not.toBeInTheDocument());
  });

  it("shows an inline error after selecting an invalid file", async () => {
    mockFetch();
    const { container } = render(<App />);

    const input = container.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(["bad"], "paper.pdf", { type: "application/pdf" });

    fireEvent.change(input, { target: { files: [file] } });

    expect(await screen.findByText("当前仅支持上传 `.docx` 文件。")).toBeInTheDocument();
  });

  it("shows source conflict when clicking upload after typing text", async () => {
    mockFetch();
    const { container } = render(<App />);
    fireEvent.change(screen.getByLabelText("论文正文输入框"), {
      target: { value: "已有内容" },
    });

    const input = container.querySelector('input[type="file"]') as HTMLInputElement;
    const clickSpy = vi.spyOn(input, "click");
    fireEvent.click(screen.getByRole("button", { name: "上传 .docx 文件" }));

    expect(clickSpy).not.toHaveBeenCalled();
    expect(await screen.findByText("请先清空当前输入，再切换输入方式。")).toBeInTheDocument();
  });

  it("shows drag-over feedback and accepts a dropped docx file", async () => {
    mockFetch();

    render(<App />);

    const textarea = screen.getByLabelText("论文正文输入框");
    const composer = textarea.closest(".composer") as HTMLElement;
    const file = new File(["docx"], "drop.docx", {
      type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    });
    const dataTransfer = {
      files: [file],
      items: [],
      types: ["Files"],
      dropEffect: "copy",
    };

    fireEvent.dragEnter(composer, { dataTransfer });
    expect(composer).toHaveAttribute("data-drag-active", "true");

    fireEvent.drop(composer, { dataTransfer });
    expect(composer).toHaveAttribute("data-drag-active", "false");
    expect(await screen.findByText("drop.docx")).toBeInTheDocument();
  });

  it("allows uploading again after clearing the previous file", async () => {
    mockFetch();
    const { container } = render(<App />);

    const input = container.querySelector('input[type="file"]') as HTMLInputElement;
    const firstFile = new File(["docx"], "paper.docx", {
      type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    });

    fireEvent.change(input, { target: { files: [firstFile] } });
    expect(await screen.findByText("paper.docx")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "清空" }));
    await waitFor(() => expect(screen.queryByText("paper.docx")).not.toBeInTheDocument());

    const secondFile = new File(["docx"], "paper.docx", {
      type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    });
    fireEvent.change(input, { target: { files: [secondFile] } });

    expect(await screen.findByText("paper.docx")).toBeInTheDocument();
  });

  it("opens preview modal after text precheck succeeds", async () => {
    mockFetch((input) => {
      const url = String(input);
      if (url.includes("/api/public/precheck/text")) return jsonResponse(samplePrecheck());
      return jsonResponse(healthPayload);
    });

    render(<App />);
    acceptPrivacy();

    fireEvent.change(screen.getByLabelText("论文正文输入框"), {
      target: { value: "结构化映射示例论文\n\n摘要\n本文展示结构化映射后的论文导出流程，并说明新的预检主线。\n\n引言\n这是足够长的正文内容，用于通过预检。".repeat(10) },
    });
    fireEvent.click(screen.getByRole("button", { name: "开始预检" }));

    expect(await screen.findByRole("dialog", { name: "导出前结构预检" })).toBeInTheDocument();
    expect(screen.getByText("结构基线已满足，可继续导出规范化 Word 文件。")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "确认并导出" })).toBeEnabled();
  });

  it("keeps input after canceling preview modal", async () => {
    mockFetch((input) => {
      const url = String(input);
      if (url.includes("/api/public/precheck/text")) return jsonResponse(samplePrecheck());
      return jsonResponse(healthPayload);
    });

    render(<App />);
    acceptPrivacy();

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

  it("keeps the composer compact after multiline input by switching to internal scrolling", async () => {
    mockFetch();

    render(<App />);

    const textarea = screen.getByLabelText("论文正文输入框") as HTMLTextAreaElement;
    let mockScrollHeight = 160;
    Object.defineProperty(textarea, "scrollHeight", {
      configurable: true,
      get: () => mockScrollHeight,
    });

    fireEvent.change(textarea, {
      target: { value: "第一行\n第二行\n第三行\n第四行\n第五行\n第六行" },
    });

    await waitFor(() => expect(Number.parseFloat(textarea.style.height)).toBeGreaterThan(0));
    expect(Number.parseFloat(textarea.style.height)).toBeLessThanOrEqual(101);
    expect(textarea.style.overflowY).toBe("auto");

    mockScrollHeight = 48;
    fireEvent.change(textarea, {
      target: { value: "第一行\n第二行" },
    });

    await waitFor(() => expect(textarea.style.overflowY).toBe("hidden"));
  });
});
