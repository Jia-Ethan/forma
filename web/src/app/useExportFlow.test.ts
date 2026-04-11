import { act, renderHook, waitFor } from "@testing-library/react";
import { useExportFlow } from "./useExportFlow";
import { validateExportReadiness } from "./domain";
import { jsonResponse, sampleThesis } from "../test/fixtures";

describe("useExportFlow", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("blocks tex export locally when required metadata is missing", async () => {
    const thesis = sampleThesis({ metadata: { title: "" } });
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);

    const { result } = renderHook(() =>
      useExportFlow({
        thesis,
        readiness: validateExportReadiness(thesis),
      }),
    );

    await act(async () => {
      await result.current.handleExport("tex");
    });

    expect(fetchMock).not.toHaveBeenCalled();
    expect(result.current.exportError?.code).toBe("FIELD_MISSING");
    expect(result.current.exportError?.message).toContain("论文题目");
  });

  it("exports with the latest thesis payload when metadata changes upstream", async () => {
    const thesis = sampleThesis({ metadata: { title: "最终题目", author_name: "李四" } });
    const fetchMock = vi.fn((_input: RequestInfo | URL, _init?: RequestInit) => jsonResponse({}));
    vi.stubGlobal("fetch", fetchMock);
    Object.defineProperty(URL, "createObjectURL", { value: vi.fn(() => "blob:texzip"), configurable: true });
    Object.defineProperty(URL, "revokeObjectURL", { value: vi.fn(), configurable: true });
    vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => undefined);

    const { result } = renderHook(() =>
      useExportFlow({
        thesis,
        readiness: validateExportReadiness(thesis),
      }),
    );

    await act(async () => {
      await result.current.handleExport("tex");
    });

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        "/api/export/texzip",
        expect.objectContaining({
          method: "POST",
          body: expect.any(String),
        }),
      );
    });

    const request = fetchMock.mock.calls[0][1] as RequestInit;
    const payload = JSON.parse(String(request.body));
    expect(payload.metadata.title).toBe("最终题目");
    expect(payload.metadata.author_name).toBe("李四");
    expect(result.current.exportToast?.title).toBe(".tex 工程 zip 已生成");
  });
});
