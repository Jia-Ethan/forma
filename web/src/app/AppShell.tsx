import { friendlyError } from "./domain";
import { useThesisWorkspace } from "./useThesisWorkspace";
import { HeroIntro, ProgressSteps, WorkspaceLayout } from "../components/layout";
import { InfoNotice, SectionCard, StatusBadge, Toast } from "../components/ui";
import { ExportPanel } from "../features/export/ExportPanel";
import { CapabilitySummary } from "../features/health/CapabilitySummary";
import { IntakePanel } from "../features/intake/IntakePanel";
import { ReviewSummary } from "../features/review/ReviewSummary";
import { ReviewWorkspace } from "../features/review/ReviewWorkspace";

export function AppShell() {
  const workspace = useThesisWorkspace();
  const error = friendlyError(workspace.error);
  const hasThesis = Boolean(workspace.thesis);

  return (
    <div className="page-shell">
      <main className="page">
        <HeroIntro health={workspace.health} />

        <section className={`workspace-section ${hasThesis ? "workspace-section-review" : "workspace-section-intake"}`} aria-labelledby="workspace-title">
          <div className="workspace-heading">
            <div>
              <p className="section-eyebrow">Workspace</p>
              <h2 id="workspace-title">{hasThesis ? "论文结构化编辑台" : "论文结构化工作区"}</h2>
            </div>
            <div className="workspace-heading-side">
              <StatusBadge tone={hasThesis ? "success" : workspace.busy ? "info" : "neutral"}>
                {hasThesis ? "Review 模式" : workspace.busy ? "识别中" : "Intake 模式"}
              </StatusBadge>
              <p>{hasThesis ? "左侧处理结构内容，右侧集中看完成度、风险和导出决策。" : "先确认输入路径和产物边界，再开始识别。"}</p>
            </div>
          </div>

          <ProgressSteps step={workspace.step} />

          {error ? (
            <InfoNotice title={error.title} tone="danger">
              <p>{error.message}</p>
              <p>{error.action}</p>
              {error.code ? <small>错误代码：{error.code}</small> : null}
            </InfoNotice>
          ) : null}

          {!workspace.thesis ? (
            <WorkspaceLayout
              main={
                <IntakePanel
                  health={workspace.health}
                  mode={workspace.mode}
                  selectedFile={workspace.selectedFile}
                  rawText={workspace.rawText}
                  busy={workspace.busy}
                  onModeChange={workspace.handleModeChange}
                  onFileChange={workspace.handleFileChange}
                  onTextChange={workspace.handleTextChange}
                  onSubmit={workspace.handleParse}
                />
              }
              side={
                <div className="side-stack">
                  <SectionCard title="开始前确认" eyebrow="Guide" tone="muted">
                    <div className="guide-list">
                      <div className="guide-item">
                        <strong>输入什么</strong>
                        <p>支持 `.docx` 上传，或直接粘贴带章节标题的正文。</p>
                      </div>
                      <div className="guide-item">
                        <strong>得到什么</strong>
                        <p>结构化 review 工作台，以及可继续编译的 `.tex` 工程 zip。</p>
                      </div>
                      <div className="guide-item">
                        <strong>不要期待什么</strong>
                        <p>当前不做线上 PDF，也不做 Word 样式一比一恢复。</p>
                      </div>
                    </div>
                  </SectionCard>
                  <CapabilitySummary health={workspace.health} compact />
                  <InfoNotice title="建议路径">
                    <p>如果 Word 文档结构复杂，优先粘贴正文获取稳定的章节骨架，再手动补字段。</p>
                  </InfoNotice>
                </div>
              }
            />
          ) : (
            <>
              <WorkspaceLayout
                main={
                  <ReviewWorkspace
                    thesis={workspace.currentThesis}
                    readiness={workspace.exportReadiness}
                    updateMetadata={workspace.updateMetadata}
                    updateAbstract={workspace.updateAbstract}
                    updateSection={workspace.updateSection}
                    addSection={workspace.addSection}
                    removeSection={workspace.removeSection}
                    updateReferences={workspace.updateReferences}
                    updateLongText={workspace.updateLongText}
                  />
                }
                side={
                  <div className="side-stack">
                    <ReviewSummary thesis={workspace.currentThesis} readiness={workspace.exportReadiness} />
                    <ExportPanel
                      thesis={workspace.currentThesis}
                      readiness={workspace.exportReadiness}
                      exporting={workspace.exporting}
                      onExport={workspace.handleExport}
                    />
                  </div>
                }
              />

              <details className="debug-panel" open={workspace.showDebug} onToggle={(event) => workspace.setShowDebug((event.currentTarget as HTMLDetailsElement).open)}>
                <summary>
                  <span>Debug JSON</span>
                  <small>开发辅助，不参与主流程</small>
                </summary>
                <pre className="debug-box">{JSON.stringify(workspace.currentThesis, null, 2)}</pre>
              </details>
            </>
          )}
        </section>
      </main>

      <Toast toast={workspace.toast} onDismiss={workspace.clearToast} />
    </div>
  );
}
