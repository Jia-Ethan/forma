import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { App } from "./App";
import type { HealthResponse, NormalizedThesis } from "./generated/contracts";

const healthPayload: HealthResponse = {
  ok: true,
  app_env: "development",
  template: "latex-scnu-web",
  capabilities: {
    tex_zip: true,
    pdf: false,
    pdf_reason: "生产环境默认关闭 PDF，请导出 tex 工程 zip。",
  },
  limits: {
    max_docx_size_bytes: 4194304,
  },
  tex: {
    xelatex: false,
    kpsewhich: false,
    missing_styles: ["ctex.sty"],
  },
};

const normalizedPayload: NormalizedThesis = {
  source_type: "text",
  metadata: {
    title: "结构化映射示例论文",
    author_name: "张三",
    student_id: "2020123456",
    department: "计算机学院",
    major: "网络工程",
    class_name: "1班",
    advisor_name: "李老师",
    submission_date: "2026-04-10",
  },
  abstract_cn: {
    content: "本文展示结构化映射后的论文导出流程。",
    keywords: ["论文模板", "结构化映射"],
  },
  abstract_en: {
    content: "This thesis demonstrates a normalized export flow.",
    keywords: ["thesis", "mapping"],
  },
  body_sections: [
    {
      id: "section-1",
      level: 1,
      title: "引言",
      content: "本章介绍系统目标。",
    },
  ],
  references: { items: ["【1】示例作者. 论文模板实践."] },
  acknowledgements: "感谢导师的指导。",
  appendix: "附录 A：补充说明。",
  warnings: [],
  parse_errors: [],
  capabilities: healthPayload.capabilities,
};

function jsonResponse(payload: unknown, ok = true) {
  return Promise.resolve({
    ok,
    statusText: ok ? "OK" : "Bad Request",
    json: async () => payload,
  } as Response);
}

function mockFetch(handler?: (input: RequestInfo | URL) => Promise<Response>) {
  const fetchMock = vi.fn((input: RequestInfo | URL) => {
    if (handler) return handler(input);
    return jsonResponse(healthPayload);
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

async function waitForHealthCard() {
  await waitFor(() => {
    expect(screen.getAllByText("latex-scnu-web")[0]).toBeInTheDocument();
  });
}

describe("App smoke", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("renders hero path and updates health capability cards", async () => {
    mockFetch();

    render(<App />);

    expect(screen.getByText("把论文内容整理成可校对、可导出的学术工作台。")).toBeInTheDocument();
    expect(screen.getAllByText("上传 .docx").length).toBeGreaterThan(0);
    expect(screen.getAllByText("粘贴正文").length).toBeGreaterThan(0);
    expect(screen.getByText("当前能力、边界与推荐路径")).toBeInTheDocument();
    expect(screen.getByText("输入内容")).toBeInTheDocument();
    expect(screen.getByText("结构识别")).toBeInTheDocument();
    expect(screen.getByText("校对修正")).toBeInTheDocument();
    expect(screen.getByText("导出成果")).toBeInTheDocument();

    await waitForHealthCard();
    expect(screen.getByText("上传上限：4 MB")).toBeInTheDocument();
    expect(screen.getAllByText("未开启")[0]).toBeInTheDocument();
  });

  it("switches segmented input modes", async () => {
    mockFetch();

    render(<App />);
    await waitForHealthCard();

    expect(screen.getByLabelText("论文文件")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("tab", { name: /粘贴正文/ }));
    expect(screen.getByLabelText("论文正文")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("tab", { name: /上传 .docx/ }));
    expect(screen.getByLabelText("论文文件")).toBeInTheDocument();
  });

  it("shows a clear message when submitting docx mode without a file", async () => {
    const fetchMock = mockFetch();

    render(<App />);
    await waitForHealthCard();
    fireEvent.click(screen.getByRole("button", { name: "开始识别" }));

    expect(await screen.findByText("文件格式不符合要求")).toBeInTheDocument();
    expect(screen.getByText("请重新选择 Word 的 .docx 文件，或切换到粘贴正文模式。")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("shows a clear message when text mode is empty", async () => {
    const fetchMock = mockFetch();

    render(<App />);
    await waitForHealthCard();
    fireEvent.click(screen.getByRole("tab", { name: /粘贴正文/ }));
    fireEvent.click(screen.getByRole("button", { name: "开始识别" }));

    expect(await screen.findByText("没有识别到可用内容")).toBeInTheDocument();
    expect(screen.getByText("请确认文件内有正文内容，或在文本框中粘贴论文正文后再试。")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("shows review workspace and PDF guidance after text parse succeeds", async () => {
    mockFetch((input) => {
      const url = String(input);
      if (url.includes("/api/normalize/text")) return jsonResponse(normalizedPayload);
      return jsonResponse(healthPayload);
    });

    render(<App />);
    await waitForHealthCard();
    fireEvent.click(screen.getByRole("tab", { name: /粘贴正文/ }));
    fireEvent.change(screen.getByLabelText("论文正文"), {
      target: { value: "# 引言\n\n这是正文。\n\n# 参考文献\n\n【1】示例作者. 论文模板实践." },
    });
    fireEvent.click(screen.getByRole("button", { name: "开始识别" }));

    expect(await screen.findByText("封面字段")).toBeInTheDocument();
    expect(screen.getByText("识别概览")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "导出 .tex 工程 zip" })).toBeEnabled();
    expect(screen.getByRole("button", { name: "导出 PDF" })).toBeDisabled();
    expect(screen.getByText("PDF 当前未开启")).toBeInTheDocument();
    expect(screen.getByLabelText("当前完成度 100%")).toBeInTheDocument();
    expect(screen.getByText("导出状态")).toBeInTheDocument();
    expect(screen.getByText("请先校对字段与章节，再导出 .tex 工程 zip。")).toBeInTheDocument();
  });
});
