import { useRef } from "react";
import type { FlowPhase, InlineErrorState } from "../../app/domain";
import type { PrecheckResponse } from "../../generated/contracts";
import { HeroAmbient } from "./HeroAmbient";
import { HomeComposer } from "./HomeComposer";
import { InlineError } from "./InlineError";
import { PrecheckResultPanel } from "./PrecheckResultPanel";

type MinimalHomeProps = {
  requirementText: string;
  selectedFile: File | null;
  phase: FlowPhase;
  precheck: PrecheckResponse | null;
  fixApplied: boolean;
  exportProgress: number;
  exportMessage?: string;
  error: InlineErrorState | null;
  canRetryExport: boolean;
  onRequirementChange: (value: string) => void;
  onUseExampleRequirement: () => void;
  onUploadTrigger: () => boolean;
  onFileSelect: (file: File | null) => void;
  onPrecheck: () => void;
  onApplyMockFix: () => void;
  onExport: () => void;
  onCancelExport: () => void;
  onRetryExport: () => void;
  onClear: () => void;
};

export function MinimalHome(props: MinimalHomeProps) {
  const heroRef = useRef<HTMLElement | null>(null);

  return (
    <main className="formatter-page">
      <nav className="portal-nav" aria-label="主导航">
        <a className="portal-brand" href="#top" aria-label="Forma 首页">
          Forma
        </a>
        <div className="portal-nav-links" aria-label="功能入口">
          <a href="#/guide">Guide</a>
          <a href="#requirements">Upload</a>
          <a href="#preview">Preview</a>
          <a href="#export">Export</a>
        </div>
      </nav>

      <section id="top" ref={heroRef} className="formatter-hero" aria-labelledby="formatter-title">
        <HeroAmbient containerRef={heroRef} />
        <div className="formatter-hero-copy">
          <p className="formatter-eyebrow">Forma</p>
          <h1 id="formatter-title" className="formatter-title">
            Format your thesis with AI.
          </h1>
          <div className="hero-actions">
            <a className="primary-action" href="#requirements">
              Start
            </a>
            <a className="secondary-action" href="#/guide">
              View guide
            </a>
          </div>
        </div>

        <section id="requirements" className="formatter-surface" aria-label="格式规范化工具">
          <HomeComposer
            requirementText={props.requirementText}
            selectedFile={props.selectedFile}
            phase={props.phase}
            onRequirementChange={props.onRequirementChange}
            onUseExampleRequirement={props.onUseExampleRequirement}
            onUploadTrigger={props.onUploadTrigger}
            onFileSelect={props.onFileSelect}
            onClear={props.onClear}
            onPrecheck={props.onPrecheck}
          />
          <InlineError
            message={props.error?.message ?? null}
            actionLabel={props.canRetryExport ? "重新导出" : undefined}
            onAction={props.canRetryExport ? props.onRetryExport : undefined}
          />
        </section>

        <div id="preview">
          <PrecheckResultPanel
            phase={props.phase}
            precheck={props.precheck}
            fixApplied={props.fixApplied}
            exportProgress={props.exportProgress}
            exportMessage={props.exportMessage}
            onApplyMockFix={props.onApplyMockFix}
            onExport={props.onExport}
            onCancelExport={props.onCancelExport}
          />
        </div>
      </section>
    </main>
  );
}
