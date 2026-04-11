import type { HealthResponse, NormalizedThesis } from "../generated/contracts";

type ThesisFixtureOverrides = Partial<Omit<NormalizedThesis, "metadata" | "abstract_cn" | "abstract_en" | "references" | "capabilities">> & {
  metadata?: Partial<NormalizedThesis["metadata"]>;
  abstract_cn?: Partial<NormalizedThesis["abstract_cn"]>;
  abstract_en?: Partial<NormalizedThesis["abstract_en"]>;
  references?: Partial<NormalizedThesis["references"]>;
  capabilities?: Partial<NormalizedThesis["capabilities"]>;
};

export const healthPayload: HealthResponse = {
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

export function sampleThesis(overrides: ThesisFixtureOverrides = {}): NormalizedThesis {
  const base: NormalizedThesis = {
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

  return {
    ...base,
    ...overrides,
    metadata: { ...base.metadata, ...overrides.metadata },
    abstract_cn: { ...base.abstract_cn, ...overrides.abstract_cn },
    abstract_en: { ...base.abstract_en, ...overrides.abstract_en },
    references: { ...base.references, ...overrides.references },
    capabilities: { ...base.capabilities, ...overrides.capabilities },
  };
}

export function jsonResponse(payload: unknown, ok = true, statusText = ok ? "OK" : "Bad Request") {
  return Promise.resolve({
    ok,
    statusText,
    json: async () => payload,
    blob: async () => new Blob(["zip"], { type: "application/zip" }),
  } as Response);
}
