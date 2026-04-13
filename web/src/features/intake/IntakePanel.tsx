import { FormEvent } from "react";
import type { HealthResponse } from "../../generated/contracts";
import type { InputMode } from "../../app/domain";
import { formatBytes, inputModeSummary } from "../../app/domain";
import { EmptyState, FieldGroup, InfoNotice, PrimaryButton, SegmentedControl, StatusBadge } from "../../components/ui";

type IntakePanelProps = {
  health: HealthResponse | null;
  mode: InputMode;
  selectedFile: File | null;
  rawText: string;
  busy: boolean;
  onModeChange: (mode: InputMode) => void;
  onFileChange: (file: File | null) => void;
  onTextChange: (value: string) => void;
  onSubmit: (event: FormEvent) => void;
};

export function IntakePanel({
  health,
  mode,
  selectedFile,
  rawText,
  busy,
  onModeChange,
  onFileChange,
  onTextChange,
  onSubmit,
}: IntakePanelProps) {
  const summary = inputModeSummary(mode);
  const hasFile = Boolean(selectedFile);

  return (
    <section className="intake-panel" aria-labelledby="intake-title">
      <div className="intake-header">
        <div>
          <p className="section-eyebrow">开始</p>
          <h2 id="intake-title">选择输入方式</h2>
          <p className="section-description">先完成输入与识别，再进入结构化编辑台统一校对。</p>
        </div>
        <div className="intake-mode-summary">
          <p className="section-eyebrow">当前入口</p>
          <strong>{summary.title}</strong>
          <p>{summary.description}</p>
        </div>
      </div>

      <SegmentedControl
        label="输入方式"
        value={mode}
        onChange={onModeChange}
        options={[
          { value: "docx", label: "上传 .docx", description: "适合已有论文文档" },
          { value: "text", label: "粘贴正文", description: "适合快速整理结构" },
        ]}
      />

      <form className="intake-form" onSubmit={onSubmit}>
        {mode === "docx" ? (
          <div className="intake-mode-panel intake-mode-panel-upload" data-has-file={hasFile ? "true" : "false"}>
            <div className="intake-mode-copy">
              <p className="section-eyebrow">上传文件</p>
              <h3>选择一个 .docx 继续</h3>
              <p>识别完成后，系统会把封面字段、摘要、章节和参考文献映射到可编辑的论文结构。</p>
            </div>

            <div className="intake-upload-box">
              <FieldGroup
                label="论文文件"
                htmlFor="docx-file"
                hint={`仅支持 .docx，当前上传上限 ${formatBytes(health?.limits.max_docx_size_bytes)}。`}
              >
                <input
                  id="docx-file"
                  type="file"
                  accept=".docx,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                  onChange={(event) => onFileChange(event.target.files?.[0] ?? null)}
                />
              </FieldGroup>

              {selectedFile ? (
                <div className="selected-file-summary" aria-live="polite">
                  <div>
                    <p className="section-eyebrow">已选文件</p>
                    <strong>{selectedFile.name}</strong>
                    <p>{formatBytes(selectedFile.size)}，已就绪，可直接开始识别。</p>
                  </div>
                  <StatusBadge tone="success">已选中</StatusBadge>
                </div>
              ) : null}
            </div>

            <EmptyState
              title={selectedFile ? "文件已就绪" : "拖入或选择 .docx 文件"}
              message={
                selectedFile
                  ? "点击开始识别后，系统会抽取可校对的论文结构，并进入 review 工作台。"
                  : "常见失败原因：上传 .doc、空文件、损坏文件，或文件超过当前大小上限。"
              }
              tone={selectedFile ? "info" : "warning"}
            />
          </div>
        ) : (
          <div className="intake-mode-panel intake-mode-panel-text">
            <FieldGroup
              label="论文正文"
              htmlFor="raw-text"
              hint="可直接粘贴带标题的文本，例如：摘要、Abstract、第一章、参考文献、致谢、附录。"
            >
              <textarea
                id="raw-text"
                rows={12}
                value={rawText}
                onChange={(event) => onTextChange(event.target.value)}
                placeholder="在这里粘贴论文正文。系统会尝试识别摘要、关键词、章节标题、参考文献、致谢与附录。"
              />
            </FieldGroup>

            <div className="intake-text-notes">
              <div>
                <p className="section-eyebrow">建议包含</p>
                <p>摘要、Abstract、章节标题、参考文献等显式标记越完整，识别结果越稳定。</p>
              </div>
              <div>
                <p className="section-eyebrow">适合场景</p>
                <p>当 Word 结构复杂或样式噪音较多时，先粘贴正文往往比直接上传更稳。</p>
              </div>
            </div>
          </div>
        )}

        <div className="intake-footer">
          <div className="intake-footer-notes">
            <InfoNotice title="当前输出" tone="info">
              <p>
                识别成功后进入结构化编辑台，最终导出的是 <code>.tex</code> 工程 zip。
              </p>
            </InfoNotice>
            <InfoNotice title="当前不会做的事" tone="warning">
              <p>不保留 Word 原始样式，不承诺复杂表格、图片、脚注或特殊排版完整恢复。</p>
            </InfoNotice>
          </div>

          <div className="intake-actions">
            <p>{busy ? "系统正在分析输入内容…" : "准备好后开始识别。识别完成会自动切换到 review 工作台。"}</p>
            <PrimaryButton type="submit" disabled={busy}>
              {busy ? "正在识别结构" : "开始识别"}
            </PrimaryButton>
          </div>
        </div>
      </form>
    </section>
  );
}
