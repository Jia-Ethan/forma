import { keywordsToString, referencesToString, reviewCompletion, reviewInsights, splitKeywords, splitReferences, validateExportReadiness } from "./domain";
import { sampleThesis } from "../test/fixtures";

describe("domain helpers", () => {
  it("keeps keywords split/stringify stable for common separators", () => {
    const input = "论文模板；结构化映射, LaTeX、导出\n校对";
    const parts = splitKeywords(input);

    expect(parts).toEqual(["论文模板", "结构化映射", "LaTeX", "导出", "校对"]);
    expect(splitKeywords(keywordsToString(parts))).toEqual(parts);
  });

  it("keeps references split/stringify stable by line", () => {
    const thesis = sampleThesis({
      references: {
        items: ["【1】示例作者. 论文模板实践.", "【2】另一作者. LaTeX 工程实践."],
      },
    });

    expect(splitReferences(referencesToString(thesis))).toEqual(thesis.references.items);
    expect(splitReferences("【1】示例作者. 论文模板实践.\n\n  【2】另一作者. LaTeX 工程实践.  ")).toEqual(thesis.references.items);
  });

  it("separates required metadata from recommended metadata", () => {
    const readiness = validateExportReadiness(
      sampleThesis({
        metadata: {
          title: "",
          class_name: "",
        },
      }),
    );

    expect(readiness.canExport).toBe(false);
    expect(readiness.missingRequired.map((item) => item.field)).toEqual(["title"]);
    expect(readiness.missingRecommended.map((item) => item.field)).toEqual(["class_name"]);
  });

  it("builds review completion and insight summaries from thesis readiness", () => {
    const thesis = sampleThesis({
      metadata: {
        title: "",
        class_name: "",
      },
      warnings: ["参考文献边界可能需要人工确认。"],
    });
    const readiness = validateExportReadiness(thesis);

    expect(reviewCompletion(thesis, readiness)).toMatchObject({
      percent: 86,
      missingRequired: 1,
      missingRecommended: 1,
    });

    expect(reviewInsights(thesis, readiness).map((item) => item.title)).toEqual([
      "导出仍被阻塞",
      "有建议补全项",
      "有结构提示待确认",
    ]);
  });
});
