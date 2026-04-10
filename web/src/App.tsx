import { FormEvent, useEffect, useMemo, useState } from "react";
import type { BodySection, HealthResponse, MetadataFields, NormalizedThesis } from "./generated/contracts";

type InputMode = "docx" | "text";

type ApiErrorPayload = {
  error_code?: string;
  error_message?: string;
};

const emptyMetadata: MetadataFields = {
  title: "",
  author_name: "",
  student_id: "",
  department: "",
  major: "",
  class_name: "",
  advisor_name: "",
  submission_date: new Date().toISOString().slice(0, 10),
};

class ApiError extends Error {
  code?: string;

  constructor(message: string, code?: string) {
    super(message);
    this.code = code;
  }
}

async function jsonRequest<T>(input: RequestInfo | URL, init?: RequestInit): Promise<T> {
  const response = await fetch(input, init);
  const data = (await response.json()) as T & ApiErrorPayload;
  if (!response.ok) {
    throw new ApiError(data.error_message || response.statusText, data.error_code);
  }
  return data as T;
}

async function blobRequest(input: RequestInfo | URL, init?: RequestInit): Promise<Blob> {
  const response = await fetch(input, init);
  if (!response.ok) {
    const payload = (await response.json()) as ApiErrorPayload;
    throw new ApiError(payload.error_message || response.statusText, payload.error_code);
  }
  return response.blob();
}

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

function keywordsToString(keywords: string[]) {
  return keywords.join("；");
}

function splitKeywords(value: string) {
  return value
    .split(/[\n，,；;、]/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function referencesToString(thesis: NormalizedThesis) {
  return thesis.references.items.join("\n");
}

function defaultThesis(health: HealthResponse | null): NormalizedThesis {
  return {
    source_type: "text",
    metadata: { ...emptyMetadata },
    abstract_cn: { content: "", keywords: [] },
    abstract_en: { content: "", keywords: [] },
    body_sections: [],
    references: { items: [] },
    acknowledgements: "",
    appendix: "",
    warnings: [],
    parse_errors: [],
    capabilities: health?.capabilities ?? {
      tex_zip: true,
      pdf: false,
      pdf_reason: "当前能力尚未加载完成。",
    },
  };
}

function StepIndicator({ active }: { active: number }) {
  const steps = ["输入", "识别", "修正", "导出"];
  return (
    <div className="stepper">
      {steps.map((step, index) => (
        <div key={step} className={index + 1 <= active ? "step active" : "step"}>
          {index + 1}. {step}
        </div>
      ))}
    </div>
  );
}

export function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [mode, setMode] = useState<InputMode>("docx");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [rawText, setRawText] = useState("");
  const [thesis, setThesis] = useState<NormalizedThesis | null>(null);
  const [busy, setBusy] = useState(false);
  const [exporting, setExporting] = useState<"tex" | "pdf" | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const [showDebug, setShowDebug] = useState(false);

  useEffect(() => {
    jsonRequest<HealthResponse>("/api/health")
      .then(setHealth)
      .catch((err) => setError(err instanceof ApiError ? err : new ApiError("健康检查失败")));
  }, []);

  const currentThesis = thesis ?? defaultThesis(health);
  const activeStep = thesis ? 4 : 1;
  const capabilityMessage = health?.capabilities.pdf_reason ?? "PDF 仅在本地开发模式中可用。";
  const bodyCount = useMemo(() => currentThesis.body_sections.length, [currentThesis.body_sections.length]);

  function resetError() {
    if (error) setError(null);
  }

  function updateMetadata(field: keyof MetadataFields, value: string) {
    setThesis((prev) => ({
      ...(prev ?? defaultThesis(health)),
      metadata: { ...(prev ?? defaultThesis(health)).metadata, [field]: value },
    }));
  }

  function updateSection(index: number, patch: Partial<BodySection>) {
    setThesis((prev) => {
      const base = prev ?? defaultThesis(health);
      const bodySections = [...base.body_sections];
      bodySections[index] = { ...bodySections[index], ...patch };
      return { ...base, body_sections: bodySections };
    });
  }

  function addSection() {
    setThesis((prev) => {
      const base = prev ?? defaultThesis(health);
      return {
        ...base,
        body_sections: [
          ...base.body_sections,
          {
            id: `manual-${Date.now()}`,
            level: 1,
            title: `新章节 ${base.body_sections.length + 1}`,
            content: "",
          },
        ],
      };
    });
  }

  function removeSection(index: number) {
    setThesis((prev) => {
      const base = prev ?? defaultThesis(health);
      return {
        ...base,
        body_sections: base.body_sections.filter((_, currentIndex) => currentIndex !== index),
      };
    });
  }

  async function handleParse(event: FormEvent) {
    event.preventDefault();
    resetError();
    setBusy(true);
    try {
      if (mode === "docx") {
        if (!selectedFile) {
          throw new ApiError("请先选择一个 .docx 文件。", "UNSUPPORTED_FILE_TYPE");
        }
        const formData = new FormData();
        formData.append("file", selectedFile);
        const parsed = await jsonRequest<NormalizedThesis>("/api/parse/docx", {
          method: "POST",
          body: formData,
        });
        setThesis({
          ...parsed,
          metadata: { ...emptyMetadata, ...parsed.metadata },
          capabilities: health?.capabilities ?? parsed.capabilities,
        });
      } else {
        const parsed = await jsonRequest<NormalizedThesis>("/api/normalize/text", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text: rawText }),
        });
        setThesis({
          ...parsed,
          metadata: { ...emptyMetadata, ...parsed.metadata },
          capabilities: health?.capabilities ?? parsed.capabilities,
        });
      }
    } catch (err) {
      setError(err instanceof ApiError ? err : new ApiError("解析失败"));
    } finally {
      setBusy(false);
    }
  }

  async function handleExport(kind: "tex" | "pdf") {
    resetError();
    setExporting(kind);
    try {
      const endpoint = kind === "tex" ? "/api/export/texzip" : "/api/export/pdf";
      const blob = await blobRequest(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(currentThesis),
      });
      const title = currentThesis.metadata.title || "scnu-thesis";
      downloadBlob(blob, kind === "tex" ? `${title}.zip` : `${title}.pdf`);
    } catch (err) {
      setError(err instanceof ApiError ? err : new ApiError("导出失败"));
    } finally {
      setExporting(null);
    }
  }

  return (
    <div className="page-shell">
      <main className="page">
        <section className="hero">
          <div className="hero-copy">
            <p className="eyebrow">SCNU Thesis Portal v0.2</p>
            <h1>把原始论文内容整理成可进入模板的规范化产物</h1>
            <p>
              当前支持上传 <code>.docx</code> 或直接粘贴正文，系统会先做结构识别，再让你在网页内补全与修正，最后导出
              规范化 <code>.tex</code> 工程 zip。
            </p>
            <ul className="plain-list muted">
              <li>仅支持 `.docx`，不支持 `.doc`</li>
              <li>不保留原 Word 样式</li>
              <li>复杂表格、图片、特殊排版未完整支持</li>
              <li>当前不是学校官方认证工具</li>
            </ul>
          </div>
          <aside className="status-card">
            <h2>当前能力</h2>
            <p>模板：{health?.template ?? "加载中"}</p>
            <p>主产物：规范化 `.tex` 工程 zip</p>
            <p>PDF：{health?.capabilities.pdf ? "已开启" : "未开启"}</p>
            <p className="muted">{capabilityMessage}</p>
            <p className="muted">上传上限：{health ? `${Math.floor(health.limits.max_docx_size_bytes / 1024 / 1024)} MB` : "加载中"}</p>
          </aside>
        </section>

        <StepIndicator active={activeStep} />

        {error ? (
          <div className="error-banner">
            <strong>{error.code ?? "ERROR"}</strong>
            <p>{error.message}</p>
          </div>
        ) : null}

        <section className="panel">
          <div className="tabs">
            <button className={mode === "docx" ? "tab active" : "tab"} type="button" onClick={() => setMode("docx")}>
              上传 `.docx`
            </button>
            <button className={mode === "text" ? "tab active" : "tab"} type="button" onClick={() => setMode("text")}>
              粘贴正文
            </button>
          </div>

          <form className="stack" onSubmit={handleParse}>
            {mode === "docx" ? (
              <label className="stack">
                <span>选择论文文件</span>
                <input
                  type="file"
                  accept=".docx"
                  onChange={(event) => {
                    setSelectedFile(event.target.files?.[0] ?? null);
                    resetError();
                  }}
                />
              </label>
            ) : (
              <label className="stack">
                <span>粘贴正文或整段论文文本</span>
                <textarea
                  rows={12}
                  value={rawText}
                  onChange={(event) => {
                    setRawText(event.target.value);
                    resetError();
                  }}
                  placeholder="可直接粘贴带标题的文本，例如：摘要 / Abstract / 第一章 / 参考文献 / 致谢 / 附录"
                />
              </label>
            )}

            <div className="actions">
              <button type="submit" disabled={busy}>
                {busy ? "识别中..." : "开始识别"}
              </button>
            </div>
          </form>
        </section>

        {thesis ? (
          <>
            <section className="grid two">
              <article className="panel">
                <h2>识别结果概览</h2>
                {currentThesis.warnings.length > 0 ? (
                  <div className="warning-card">
                    <strong>Warnings</strong>
                    <ul className="plain-list">
                      {currentThesis.warnings.map((warning) => (
                        <li key={warning}>{warning}</li>
                      ))}
                    </ul>
                  </div>
                ) : null}
                {currentThesis.parse_errors.length > 0 ? (
                  <div className="error-card">
                    <strong>Parse Errors</strong>
                    <ul className="plain-list">
                      {currentThesis.parse_errors.map((message) => (
                        <li key={message}>{message}</li>
                      ))}
                    </ul>
                  </div>
                ) : null}
                <ul className="plain-list">
                  <li>中文摘要：{currentThesis.abstract_cn.content ? "已识别" : "待补充"}</li>
                  <li>Abstract：{currentThesis.abstract_en.content ? "已识别" : "待补充"}</li>
                  <li>正文章节：{bodyCount} 个</li>
                  <li>参考文献：{currentThesis.references.items.length} 条</li>
                  <li>致谢：{currentThesis.acknowledgements ? "已识别" : "待补充"}</li>
                  <li>附录：{currentThesis.appendix ? "已识别" : "待补充"}</li>
                </ul>
              </article>

              <article className="panel">
                <h2>导出说明</h2>
                <p>线上首轮默认主产物是规范化 `.tex` 工程 zip，方便你继续人工调整与本地编译。</p>
                <div className="actions">
                  <button type="button" onClick={() => handleExport("tex")} disabled={exporting !== null}>
                    {exporting === "tex" ? "导出中..." : "导出 .tex 工程 zip"}
                  </button>
                  {currentThesis.capabilities.pdf ? (
                    <button type="button" className="secondary-button" onClick={() => handleExport("pdf")} disabled={exporting !== null}>
                      {exporting === "pdf" ? "导出中..." : "导出 PDF"}
                    </button>
                  ) : (
                    <button type="button" className="secondary-button" disabled>
                      PDF 当前未开启
                    </button>
                  )}
                </div>
                {!currentThesis.capabilities.pdf ? <p className="muted">{currentThesis.capabilities.pdf_reason}</p> : null}
              </article>
            </section>

            <section className="panel">
              <h2>字段补全与修正</h2>
              <div className="form-grid">
                {(
                  [
                    ["title", "论文题目"],
                    ["author_name", "学生姓名"],
                    ["student_id", "学号"],
                    ["department", "学院 / 系别"],
                    ["major", "专业"],
                    ["class_name", "班级"],
                    ["advisor_name", "指导老师"],
                    ["submission_date", "提交日期"],
                  ] as [keyof MetadataFields, string][]
                ).map(([field, label]) => (
                  <label key={field}>
                    <span>{label}</span>
                    <input value={currentThesis.metadata[field] ?? ""} onChange={(event) => updateMetadata(field, event.target.value)} />
                  </label>
                ))}
              </div>
            </section>

            <section className="grid two">
              <article className="panel">
                <h2>中文摘要</h2>
                <label>
                  <span>摘要</span>
                  <textarea
                    rows={8}
                    value={currentThesis.abstract_cn.content}
                    onChange={(event) =>
                      setThesis((prev) => ({
                        ...(prev ?? defaultThesis(health)),
                        abstract_cn: { ...currentThesis.abstract_cn, content: event.target.value },
                      }))
                    }
                  />
                </label>
                <label>
                  <span>关键词</span>
                  <input
                    value={keywordsToString(currentThesis.abstract_cn.keywords)}
                    onChange={(event) =>
                      setThesis((prev) => ({
                        ...(prev ?? defaultThesis(health)),
                        abstract_cn: { ...currentThesis.abstract_cn, keywords: splitKeywords(event.target.value) },
                      }))
                    }
                  />
                </label>
              </article>

              <article className="panel">
                <h2>Abstract</h2>
                <label>
                  <span>Abstract</span>
                  <textarea
                    rows={8}
                    value={currentThesis.abstract_en.content}
                    onChange={(event) =>
                      setThesis((prev) => ({
                        ...(prev ?? defaultThesis(health)),
                        abstract_en: { ...currentThesis.abstract_en, content: event.target.value },
                      }))
                    }
                  />
                </label>
                <label>
                  <span>Keywords</span>
                  <input
                    value={keywordsToString(currentThesis.abstract_en.keywords)}
                    onChange={(event) =>
                      setThesis((prev) => ({
                        ...(prev ?? defaultThesis(health)),
                        abstract_en: { ...currentThesis.abstract_en, keywords: splitKeywords(event.target.value) },
                      }))
                    }
                  />
                </label>
              </article>
            </section>

            <section className="panel">
              <div className="section-header">
                <h2>正文章节</h2>
                <button type="button" className="secondary-button" onClick={addSection}>
                  新增章节
                </button>
              </div>
              <div className="stack">
                {currentThesis.body_sections.map((section, index) => (
                  <article className="section-card" key={section.id}>
                    <div className="section-row">
                      <label>
                        <span>层级</span>
                        <select
                          value={section.level}
                          onChange={(event) => updateSection(index, { level: Number(event.target.value) })}
                        >
                          <option value={1}>一级标题</option>
                          <option value={2}>二级标题</option>
                          <option value={3}>三级标题</option>
                        </select>
                      </label>
                      <button type="button" className="ghost-button" onClick={() => removeSection(index)}>
                        删除
                      </button>
                    </div>
                    <label>
                      <span>章节标题</span>
                      <input value={section.title} onChange={(event) => updateSection(index, { title: event.target.value })} />
                    </label>
                    <label>
                      <span>章节内容</span>
                      <textarea
                        rows={8}
                        value={section.content}
                        onChange={(event) => updateSection(index, { content: event.target.value })}
                      />
                    </label>
                  </article>
                ))}
              </div>
            </section>

            <section className="grid two">
              <article className="panel">
                <h2>参考文献</h2>
                <label>
                  <span>每行一条</span>
                  <textarea
                    rows={10}
                    value={referencesToString(currentThesis)}
                    onChange={(event) =>
                      setThesis((prev) => ({
                        ...(prev ?? defaultThesis(health)),
                        references: {
                          items: event.target.value.split("\n").map((item) => item.trim()).filter(Boolean),
                        },
                      }))
                    }
                  />
                </label>
              </article>

              <article className="panel">
                <h2>致谢与附录</h2>
                <label>
                  <span>致谢</span>
                  <textarea
                    rows={5}
                    value={currentThesis.acknowledgements}
                    onChange={(event) =>
                      setThesis((prev) => ({
                        ...(prev ?? defaultThesis(health)),
                        acknowledgements: event.target.value,
                      }))
                    }
                  />
                </label>
                <label>
                  <span>附录</span>
                  <textarea
                    rows={5}
                    value={currentThesis.appendix}
                    onChange={(event) =>
                      setThesis((prev) => ({
                        ...(prev ?? defaultThesis(health)),
                        appendix: event.target.value,
                      }))
                    }
                  />
                </label>
              </article>
            </section>

            <section className="panel">
              <div className="section-header">
                <h2>调试信息</h2>
                <button type="button" className="secondary-button" onClick={() => setShowDebug((prev) => !prev)}>
                  {showDebug ? "隐藏" : "显示"} JSON
                </button>
              </div>
              {showDebug ? <pre className="debug-box">{JSON.stringify(currentThesis, null, 2)}</pre> : null}
            </section>
          </>
        ) : null}
      </main>
    </div>
  );
}
