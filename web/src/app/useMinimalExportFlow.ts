import { useEffect, useMemo, useState } from "react";
import type { HealthResponse, PrecheckResponse } from "../generated/contracts";
import { ApiError, downloadBlob, exportDocx, getHealth, precheckDocx, precheckText } from "./api";
import { exportFilename, inferPhase, mapApiError, validateDocxFile, validateTextInput, type FlowPhase, type InlineErrorState } from "./domain";

const EXPORT_MIN_DURATION_MS = typeof navigator !== "undefined" && /jsdom/i.test(navigator.userAgent) ? 20 : 4200;

export function useMinimalExportFlow() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [rawText, setRawText] = useState("");
  const [busy, setBusy] = useState(false);
  const [previewModalOpen, setPreviewModalOpen] = useState(false);
  const [precheck, setPrecheck] = useState<PrecheckResponse | null>(null);
  const [exporting, setExporting] = useState(false);
  const [exportProgress, setExportProgress] = useState(0);
  const [inlineError, setInlineError] = useState<InlineErrorState | null>(null);

  useEffect(() => {
    getHealth()
      .then((response) => {
        setHealth(response);
      })
      .catch((error) => setInlineError(mapApiError(error instanceof ApiError ? error : new ApiError("健康检查失败", "NETWORK_ERROR"))));
  }, []);

  useEffect(() => {
    if (!exporting) {
      setExportProgress(0);
      return;
    }

    setExportProgress(0);
    const timer = window.setInterval(() => {
      setExportProgress((current) => {
        if (current >= 92) return current;
        const next = current + Math.max(1.5, (92 - current) * 0.11);
        return Math.min(next, 92);
      });
    }, 120);

    return () => window.clearInterval(timer);
  }, [exporting]);

  const phase: FlowPhase = useMemo(
    () => inferPhase(rawText, selectedFile, busy, previewModalOpen, exporting),
    [busy, exporting, previewModalOpen, rawText, selectedFile],
  );

  function clearAll() {
    setSelectedFile(null);
    setRawText("");
    setBusy(false);
    setPreviewModalOpen(false);
    setPrecheck(null);
    setExporting(false);
    setExportProgress(0);
    setInlineError(null);
  }

  function resetResult() {
    if (precheck) setPrecheck(null);
    if (previewModalOpen) setPreviewModalOpen(false);
  }

  function handleUploadTrigger() {
    if (busy || exporting) return false;
    if (rawText.trim()) {
      setInlineError({ message: "请先清空当前输入，再切换输入方式。", code: "SOURCE_CONFLICT" });
      return false;
    }
    setInlineError(null);
    return true;
  }

  function handleFileSelect(file: File | null) {
    if (rawText.trim()) {
      setInlineError({ message: "请先清空当前输入，再切换输入方式。", code: "SOURCE_CONFLICT" });
      return;
    }
    resetResult();
    const validation = validateDocxFile(file);
    if (validation && file) {
      setSelectedFile(null);
      setInlineError(validation);
      return;
    }
    setInlineError(null);
    setSelectedFile(file);
  }

  function handleTextChange(value: string) {
    if (selectedFile && value.trim()) {
      setInlineError({ message: "请先清空当前输入，再切换输入方式。", code: "SOURCE_CONFLICT" });
      return;
    }
    resetResult();
    setInlineError(null);
    setRawText(value);
  }

  async function handlePrecheck() {
    setInlineError(null);
    resetResult();

    const validation = selectedFile ? validateDocxFile(selectedFile) : validateTextInput(rawText);
    if (validation) {
      setInlineError(validation);
      return;
    }

    setBusy(true);
    try {
      const response = selectedFile ? await precheckDocx(selectedFile) : await precheckText(rawText);
      setPrecheck(response);
      setPreviewModalOpen(true);
    } catch (error) {
      setInlineError(mapApiError(error instanceof ApiError ? error : new ApiError("预检失败", "PARSE_FAILED")));
    } finally {
      setBusy(false);
    }
  }

  function handleCancelPreview() {
    setPreviewModalOpen(false);
  }

  async function handleConfirmExport() {
    if (!precheck?.summary.can_confirm) {
      setInlineError({ message: precheck?.summary.blocking_message || "预检仍存在阻塞项，暂时无法导出。", code: "FIELD_MISSING" });
      return;
    }

    setInlineError(null);
    setPreviewModalOpen(false);
    setExporting(true);

    try {
      const minDelay = new Promise((resolve) => window.setTimeout(resolve, EXPORT_MIN_DURATION_MS));
      const [blob] = await Promise.all([exportDocx(precheck.thesis), minDelay]);
      setExportProgress(100);
      downloadBlob(blob, exportFilename(precheck.thesis));
      await new Promise((resolve) => window.setTimeout(resolve, 220));
      clearAll();
    } catch (error) {
      setExporting(false);
      setInlineError(mapApiError(error instanceof ApiError ? error : new ApiError("导出失败", "EXPORT_FAILED")));
    }
  }

  return {
    health,
    selectedFile,
    rawText,
    phase,
    busy,
    previewModalOpen,
    precheck,
    exporting,
    exportProgress,
    inlineError,
    clearAll,
    handleFileSelect,
    handleUploadTrigger,
    handleTextChange,
    handlePrecheck,
    handleCancelPreview,
    handleConfirmExport,
  };
}
