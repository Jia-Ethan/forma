import { exportFilename, inferPhase, mapApiError, validateDocxFile, validateTextInput } from "./domain";
import { ApiError } from "./api";
import { sampleThesis } from "../test/fixtures";

describe("domain helpers", () => {
  it("maps flow phases from source and status", () => {
    expect(inferPhase("", null, false, false, false)).toBe("idle");
    expect(inferPhase("正文", null, false, false, false)).toBe("text_ready");
    expect(inferPhase("", new File(["ok"], "paper.docx"), false, false, false)).toBe("file_ready");
    expect(inferPhase("", null, true, false, false)).toBe("prechecking");
    expect(inferPhase("", null, false, true, false)).toBe("preview_modal_open");
    expect(inferPhase("", null, false, false, true)).toBe("exporting");
  });

  it("validates local input before request", () => {
    expect(validateTextInput("   ")?.code).toBe("CONTENT_EMPTY");
    expect(validateDocxFile(new File(["bad"], "notes.txt"))?.code).toBe("UNSUPPORTED_FILE_TYPE");
    expect(validateDocxFile(new File(["ok"], "paper.docx"))).toBeNull();
  });

  it("maps backend errors and computes safe docx filenames", () => {
    expect(mapApiError(new ApiError("导出失败", "EXPORT_FAILED"))?.message).toBe("导出失败，请稍后重试。");
    expect(exportFilename(sampleThesis({ metadata: { title: '论文:<>?"测试' } }))).toBe("论文-----测试.docx");
  });
});
