import { useState, type FormEvent } from "react";
import { ApiError, verifyAccessCode } from "../app/api";

type AccessCodeGateProps = {
  onVerified: () => void;
};

export function AccessCodeGate({ onVerified }: AccessCodeGateProps) {
  const [accessCode, setAccessCode] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setMessage(null);
    try {
      const result = await verifyAccessCode(accessCode);
      if (result.verified) onVerified();
    } catch (error) {
      setMessage(error instanceof ApiError ? error.message : "访问码验证失败。");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="workbench-gate">
      <form className="workbench-gate-card" onSubmit={(event) => void handleSubmit(event)}>
        <a className="workbench-back" href="#/">
          返回快速导出
        </a>
        <h1>SCNU Thesis Agent Workbench</h1>
        <p>该部署已启用访问码保护。验证后再进入项目、文件和 Provider 设置。</p>
        <label>
          访问码
          <input value={accessCode} onChange={(event) => setAccessCode(event.target.value)} type="password" autoFocus />
        </label>
        {message ? <p className="workbench-message is-error">{message}</p> : null}
        <button type="submit" disabled={busy || !accessCode.trim()}>
          {busy ? "验证中" : "进入 Workbench"}
        </button>
      </form>
    </main>
  );
}
