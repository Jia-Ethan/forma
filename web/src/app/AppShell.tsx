import { MinimalHome } from "../components/minimal/MinimalHome";
import { PrecheckModal } from "../components/minimal/PrecheckModal";
import { useMinimalExportFlow } from "./useMinimalExportFlow";

export function AppShell() {
  const flow = useMinimalExportFlow();

  return (
    <>
      <MinimalHome
        rawText={flow.rawText}
        selectedFile={flow.selectedFile}
        phase={flow.phase}
        exportProgress={flow.exportProgress}
        error={flow.inlineError}
        onTextChange={flow.handleTextChange}
        onFileSelect={flow.handleFileSelect}
        onSubmit={flow.handlePrecheck}
        onClear={flow.clearAll}
      />
      <PrecheckModal open={flow.previewModalOpen} precheck={flow.precheck} onCancel={flow.handleCancelPreview} onConfirm={flow.handleConfirmExport} />
    </>
  );
}
