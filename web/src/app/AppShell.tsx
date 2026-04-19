import { useEffect, useState } from "react";
import { MinimalHome } from "../components/minimal/MinimalHome";
import { PrecheckModal } from "../components/minimal/PrecheckModal";
import { WorkbenchApp } from "../workbench/WorkbenchApp";
import { WorkbenchDemo } from "../workbench/WorkbenchDemo";
import { useMinimalExportFlow } from "./useMinimalExportFlow";

export function AppShell() {
  const [route, setRoute] = useState(() => window.location.hash || "#/");

  useEffect(() => {
    const handler = () => setRoute(window.location.hash || "#/");
    window.addEventListener("hashchange", handler);
    return () => window.removeEventListener("hashchange", handler);
  }, []);

  if (route === "#/workbench") {
    return <WorkbenchApp />;
  }

  if (route === "#/workbench-demo") {
    return <WorkbenchDemo />;
  }

  if (route === "#/en") {
    return <EnglishHome />;
  }

  return <HomeRoute />;
}

function HomeRoute() {
  const flow = useMinimalExportFlow();

  return (
    <>
      <MinimalHome
        rawText={flow.rawText}
        selectedFile={flow.selectedFile}
        phase={flow.phase}
        exportProgress={flow.exportProgress}
        error={flow.inlineError}
        privacyAccepted={flow.privacyAccepted}
        turnstileToken={flow.turnstileToken}
        onTextChange={flow.handleTextChange}
        onUploadTrigger={flow.handleUploadTrigger}
        onFileSelect={flow.handleFileSelect}
        onSubmit={flow.handlePrecheck}
        onClear={flow.clearAll}
        onPrivacyAcceptedChange={flow.setPrivacyAccepted}
        onTurnstileTokenChange={flow.setTurnstileToken}
      />
      <PrecheckModal open={flow.previewModalOpen} precheck={flow.precheck} onCancel={flow.handleCancelPreview} onConfirm={flow.handleConfirmExport} />
    </>
  );
}

function EnglishHome() {
  return (
    <main className="public-page">
      <section className="public-section public-boundary" aria-labelledby="english-title">
        <div>
          <p className="public-kicker">SCNU Thesis Agent Workbench</p>
          <h1 id="english-title">SCNU undergraduate thesis formatting and export workbench</h1>
          <p>
            This project is not an official university service and does not write theses for students. The public site focuses on `.docx`
            precheck and normalized Word export. Remote AI providers are disabled on the public entry.
          </p>
        </div>
        <div className="public-boundary-grid">
          <article>
            <h2>Quick Export</h2>
            <p>Upload an existing `.docx` or paste existing thesis text for format precheck, then export a normalized Word document.</p>
          </article>
          <article>
            <h2>Privacy</h2>
            <p>Uploaded material is processed for the export flow. Export files are retained for 30 minutes.</p>
          </article>
          <article>
            <h2>Workbench Demo</h2>
            <p>The demo project is interactive but does not store real thesis content or call remote providers.</p>
          </article>
          <article>
            <h2>Self-host</h2>
            <p>Real projects should run behind an access code on a private Docker Compose deployment.</p>
          </article>
        </div>
        <nav className="public-hero-actions" aria-label="English page links">
          <a href="#/">中文主页</a>
          <a href="#/workbench-demo">Workbench Demo</a>
          <a href="https://github.com/Jia-Ethan/scnu-thesis-portal" target="_blank" rel="noreferrer">GitHub</a>
        </nav>
      </section>
    </main>
  );
}
