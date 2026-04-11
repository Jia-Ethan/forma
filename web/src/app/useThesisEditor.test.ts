import { act, renderHook } from "@testing-library/react";
import { useThesisEditor } from "./useThesisEditor";
import { healthPayload, sampleThesis } from "../test/fixtures";

describe("useThesisEditor", () => {
  it("updates metadata, references, and sections without losing current thesis state", () => {
    const { result } = renderHook(() => useThesisEditor(healthPayload));

    act(() => {
      result.current.setParsedThesis(sampleThesis());
    });

    act(() => {
      result.current.updateMetadata("title", "更新后的题目");
      result.current.updateReferences(["【1】更新后的参考文献."]);
      result.current.addSection();
    });

    const addedIndex = result.current.currentThesis.body_sections.length - 1;

    act(() => {
      result.current.updateSection(addedIndex, {
        title: "新增章节标题",
        content: "新增章节内容。",
      });
      result.current.removeSection(0);
    });

    expect(result.current.currentThesis.metadata.title).toBe("更新后的题目");
    expect(result.current.currentThesis.references.items).toEqual(["【1】更新后的参考文献."]);
    expect(result.current.currentThesis.body_sections).toHaveLength(1);
    expect(result.current.currentThesis.body_sections[0].title).toBe("新增章节标题");
    expect(result.current.currentThesis.body_sections[0].content).toBe("新增章节内容。");
  });
});
