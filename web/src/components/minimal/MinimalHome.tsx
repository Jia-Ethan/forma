import { useRef, useState } from "react";
import type { FlowPhase, InlineErrorState } from "../../app/domain";
import { HeroAmbient } from "./HeroAmbient";
import { HomeComposer } from "./HomeComposer";
import { InlineError } from "./InlineError";

type MinimalHomeProps = {
  rawText: string;
  selectedFile: File | null;
  phase: FlowPhase;
  exportProgress: number;
  error: InlineErrorState | null;
  onTextChange: (value: string) => void;
  onUploadTrigger: () => boolean;
  onFileSelect: (file: File | null) => void;
  onSubmit: () => void;
  onClear: () => void;
};

export function MinimalHome(props: MinimalHomeProps) {
  const heroRef = useRef<HTMLElement | null>(null);
  const [isDragActive, setIsDragActive] = useState(false);
  const hasContent = Boolean(props.selectedFile || props.rawText.trim());
  const isBusy = props.phase === "prechecking" || props.phase === "exporting";

  return (
    <main className="minimal-page">
      <section
        ref={heroRef}
        className="minimal-hero"
        aria-labelledby="sc-th-title"
        data-has-content={hasContent}
        data-drag-active={isDragActive}
        data-busy={isBusy}
      >
        <HeroAmbient containerRef={heroRef} />
        <h1 id="sc-th-title" className="minimal-logo">
          SC-TH
        </h1>
        <HomeComposer
          rawText={props.rawText}
          selectedFile={props.selectedFile}
          phase={props.phase}
          exportProgress={props.exportProgress}
          onTextChange={props.onTextChange}
          onUploadTrigger={props.onUploadTrigger}
          onFileSelect={props.onFileSelect}
          onSubmit={props.onSubmit}
          onClear={props.onClear}
          onDragActiveChange={setIsDragActive}
        />
        <InlineError message={props.error?.message ?? null} />
      </section>
    </main>
  );
}
