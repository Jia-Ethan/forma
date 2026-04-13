import type { HealthResponse, NormalizedThesis, PrecheckResponse } from "../generated/contracts";

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
  template: "sc-th-word",
  capabilities: {
    docx_export: true,
    profile: "undergraduate",
  },
  limits: {
    max_docx_size_bytes: 4194304,
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
      content:
        "本文展示结构化映射后的论文导出流程，并说明如何在极简入口下完成一次完整的本科论文结构预检、风险暴露与 Word 文档导出。系统优先保障题目、摘要、正文结构与参考文献的最小可交付性，再通过统一模板输出结果。",
      keywords: ["论文模板", "结构化映射", "Word 导出"],
    },
    abstract_en: {
      content:
        "This thesis demonstrates a minimal precheck flow that validates title, abstract, body structure, and references before exporting a formatted Word thesis document.",
      keywords: ["thesis", "word export", "precheck"],
    },
    body_sections: [
      {
        id: "section-1",
        level: 1,
        title: "引言",
        content:
          "本章介绍系统目标、输入方式与预检原则。为了满足新的 Word 导出主线，系统会在导出前先完成结构识别、摘要校验、正文长度判断和参考文献存在性检查。通过预检后，用户无需再进入复杂工作台，只需等待导出完成即可。",
      },
      {
        id: "section-2",
        level: 1,
        title: "实现路径",
        content:
          "实现层需要把解析结果映射为统一的论文结构对象，再由预检规则层输出阻塞项、警告项和信息项。前端只负责展示这些结果，并在确认后触发 Word 模板导出。这样既能缩短主路径，也能让错误前置暴露，避免黑盒直出带来的不确定性。",
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

export function samplePrecheck(overrides: Partial<PrecheckResponse> = {}): PrecheckResponse {
  const thesis = overrides.thesis ?? sampleThesis();
  return {
    thesis,
    summary: {
      can_confirm: true,
      blocking_count: 0,
      warning_count: 2,
      info_count: 2,
      blocking_message: "预检已通过，可以开始导出 Word 文件。",
      warning_message: "另有 2 项警告不影响继续导出。",
    },
    issues: [
      {
        id: "metadata-missing",
        code: "COVER_FIELDS_MISSING",
        severity: "warning",
        block: "metadata",
        title: "封面字段待补充",
        message: "以下字段仍未识别：班级。",
      },
      {
        id: "docx-export-profile",
        code: "DOCX_EXPORT_PROFILE",
        severity: "info",
        block: "metadata",
        title: "导出配置",
        message: "导出将按 SC-TH 本科论文 Word 模板生成。",
      },
      {
        id: "body-section-count",
        code: "BODY_SECTION_COUNT",
        severity: "info",
        block: "body",
        title: "章节识别概览",
        message: "当前识别到 2 个正文结构块。",
      },
    ],
    preview_blocks: [
      {
        key: "title",
        label: "题目",
        status: "ok",
        preview: thesis.metadata.title,
        issue_ids: [],
      },
      {
        key: "abstract_cn",
        label: "中文摘要",
        status: "ok",
        preview: thesis.abstract_cn.content.slice(0, 50),
        issue_ids: [],
      },
      {
        key: "abstract_en",
        label: "英文摘要",
        status: "ok",
        preview: thesis.abstract_en.content.slice(0, 50),
        issue_ids: [],
      },
      {
        key: "keywords",
        label: "关键词",
        status: "ok",
        preview: thesis.abstract_cn.keywords.join("；"),
        issue_ids: [],
      },
      {
        key: "body",
        label: "正文结构",
        status: "ok",
        preview: "引言 / 实现路径 （共 2 个结构块）",
        issue_ids: ["body-section-count"],
      },
      {
        key: "references",
        label: "参考文献",
        status: "ok",
        preview: thesis.references.items[0],
        issue_ids: [],
      },
      {
        key: "acknowledgements",
        label: "致谢",
        status: "ok",
        preview: thesis.acknowledgements,
        issue_ids: [],
      },
      {
        key: "appendix",
        label: "附录",
        status: "ok",
        preview: thesis.appendix,
        issue_ids: [],
      },
      {
        key: "metadata",
        label: "封面字段",
        status: "warning",
        preview: "已识别 6/7 项：学生姓名、学号、学院、专业、指导老师、提交日期",
        issue_ids: ["metadata-missing", "docx-export-profile"],
      },
    ],
    ...overrides,
  };
}

export function jsonResponse(payload: unknown, ok = true, statusText = ok ? "OK" : "Bad Request") {
  return Promise.resolve({
    ok,
    statusText,
    json: async () => payload,
    blob: async () => new Blob(["docx"], { type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document" }),
  } as Response);
}
