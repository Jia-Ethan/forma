import type { FlowPhase, InlineErrorState } from "../../app/domain";
import { HomeComposer } from "./HomeComposer";
import { InlineError } from "./InlineError";

type MinimalHomeProps = {
  rawText: string;
  selectedFile: File | null;
  phase: FlowPhase;
  exportProgress: number;
  error: InlineErrorState | null;
  onTextChange: (value: string) => void;
  onFileSelect: (file: File | null) => void;
  onSubmit: () => void;
  onClear: () => void;
};

export function MinimalHome(props: MinimalHomeProps) {
  return (
    <main className="minimal-page">
      <section className="minimal-hero" aria-labelledby="sc-th-title">
        <p className="minimal-logo">SC-TH</p>
        <h1 id="sc-th-title">极简论文预检与 Word 导出</h1>
        <HomeComposer
          rawText={props.rawText}
          selectedFile={props.selectedFile}
          phase={props.phase}
          exportProgress={props.exportProgress}
          onTextChange={props.onTextChange}
          onFileSelect={props.onFileSelect}
          onSubmit={props.onSubmit}
          onClear={props.onClear}
        />
        <InlineError message={props.error?.message ?? null} />
      </section>
    </main>
  );
}
