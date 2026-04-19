import type { HealthResponse, NormalizedThesis, PrecheckResponse } from "../generated/contracts";

type ThesisFixtureOverrides = Partial<Omit<NormalizedThesis, "cover" | "abstract_cn" | "abstract_en" | "capabilities" | "source_features">> & {
  cover?: Partial<NormalizedThesis["cover"]>;
  abstract_cn?: Partial<NormalizedThesis["abstract_cn"]>;
  abstract_en?: Partial<NormalizedThesis["abstract_en"]>;
  capabilities?: Partial<NormalizedThesis["capabilities"]>;
  source_features?: Partial<NormalizedThesis["source_features"]>;
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
    max_docx_size_bytes: 20971520,
    max_text_precheck_chars: 80000,
  },
};

export function sampleThesis(overrides: ThesisFixtureOverrides = {}): NormalizedThesis {
  const base: NormalizedThesis = {
    schema_version: "2",
    revision_id: null,
    source_type: "text",
    cover: {
      title: "结构化映射示例论文",
      advisor: "李老师",
      student_name: "张三",
      student_id: "2020123456",
      school: "华南师范大学",
      department: "计算机学院",
      major: "网络工程",
      class_name: "1班",
      graduation_time: "2026年6月",
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
        level: 2,
        title: "实现路径",
        content:
          "实现层需要把解析结果映射为统一的论文结构对象，再由预检规则层输出阻塞项、警告项和信息项。前端只负责展示这些结果，并在确认后触发 Word 模板导出。这样既能缩短主路径，也能让错误前置暴露，避免黑盒直出带来的不确定性。",
      },
    ],
    references: [{ raw_text: "【1】示例作者. 论文模板实践.", normalized_text: "示例作者. 论文模板实践.", detected_type: "J" }],
    appendices: [{ id: "appendix-1", title: "附录 A：补充说明", content: "附录 A：补充说明。" }],
    acknowledgements: "感谢导师的指导。",
    notes: "",
    warnings: [],
    manual_review_flags: [],
    missing_sections: [],
    source_features: {
      table_count: 0,
      image_count: 0,
      footnote_count: 0,
      textbox_count: 0,
      shape_count: 0,
      field_count: 0,
      rich_run_count: 0,
    },
    capabilities: healthPayload.capabilities,
    blocks: [],
    source_spans: [],
    provenance: [],
    confidence: 1,
    comments: [],
    format_risks: [],
  };

  return {
    ...base,
    ...overrides,
    cover: { ...base.cover, ...overrides.cover },
    abstract_cn: { ...base.abstract_cn, ...overrides.abstract_cn },
    abstract_en: { ...base.abstract_en, ...overrides.abstract_en },
    source_features: { ...base.source_features, ...overrides.source_features },
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
      blocking_message: "结构基线已满足，可继续导出规范化 Word 文件。",
      warning_message: "另有 2 项警告，其中缺失章节会按留白位保留，复杂元素需人工复核。",
    },
    issues: [
      {
        id: "cover-fields-missing",
        code: "COVER_FIELDS_MISSING",
        severity: "warning",
        block: "cover",
        title: "封面字段将留白",
        message: "以下封面字段未识别，将按学校格式保留下划线或留白：班级。",
        block_id: null,
        source_span: null,
        rule_source_id: null,
        suggested_action: null,
      },
      {
        id: "docx-export-profile",
        code: "DOCX_EXPORT_PROFILE",
        severity: "info",
        block: "cover",
        title: "导出主线",
        message: "导出将按“学校规范 PDF > 学生手册补充 > main.pdf > 旧实现”的仲裁规则生成本科论文 Word 文件。",
        block_id: null,
        source_span: null,
        rule_source_id: null,
        suggested_action: null,
      },
      {
        id: "body-section-count",
        code: "BODY_SECTION_COUNT",
        severity: "info",
        block: "body",
        title: "章节识别概览",
        message: "当前识别到 2 个正文章节块，将固定生成目录、分节和页码。",
        block_id: null,
        source_span: null,
        rule_source_id: null,
        suggested_action: null,
      },
    ],
    preview_blocks: [
      {
        key: "cover",
        label: "正式封面",
        status: "warning",
        preview: "已识别 7/8 项：论文题目、指导教师、学生姓名、学号、学院、专业、毕业时间",
        issue_ids: ["cover-fields-missing", "docx-export-profile"],
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
        preview: thesis.references[0]?.normalized_text || "",
        issue_ids: [],
      },
      {
        key: "appendices",
        label: "附录",
        status: "ok",
        preview: thesis.appendices[0]?.title || "",
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
        key: "notes",
        label: "注释",
        status: "ok",
        preview: thesis.notes || "未识别到注释章节",
        issue_ids: [],
      },
      {
        key: "complex_elements",
        label: "复杂元素",
        status: "ok",
        preview: "未检测到需人工复核的复杂元素",
        issue_ids: [],
      },
    ],
    export_token: "v1:9999999999:test:signature",
    expires_at: "2099-01-01T00:00:00",
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
