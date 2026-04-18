import { useState, type FormEvent } from "react";
import type { ProviderConfigRecord, ProviderOption } from "../app/api";

type ProviderSettingsProps = {
  providers: ProviderOption[];
  configs: ProviderConfigRecord[];
  remoteAllowed: boolean;
  busy?: boolean;
  onSave: (payload: { provider: string; model: string; base_url?: string; api_key?: string; allow_local?: boolean }) => Promise<void>;
  onVerify: (configId: string) => Promise<void>;
  onDelete: (configId: string) => Promise<void>;
};

export function ProviderSettings({ providers, configs, remoteAllowed, busy = false, onSave, onVerify, onDelete }: ProviderSettingsProps) {
  const [provider, setProvider] = useState("ollama");
  const [model, setModel] = useState("");
  const [baseUrl, setBaseUrl] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [allowLocal, setAllowLocal] = useState(true);
  const selected = providers.find((item) => item.id === provider);
  const isRemote = selected?.remote ?? false;
  const disabledByPrivacy = isRemote && !remoteAllowed;

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await onSave({
      provider,
      model,
      base_url: baseUrl || undefined,
      api_key: apiKey || undefined,
      allow_local: provider === "ollama" && allowLocal,
    });
    setApiKey("");
  }

  return (
    <section className="provider-settings">
      <h3>Provider 设置</h3>
      <form onSubmit={(event) => void handleSubmit(event)}>
        <div className="workbench-form-grid">
          <label>
            Provider
            <select value={provider} onChange={(event) => setProvider(event.target.value)}>
              {providers.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name} · {item.remote ? "远程" : "本地"}
                </option>
              ))}
            </select>
          </label>
          <label>
            模型
            <input value={model} onChange={(event) => setModel(event.target.value)} placeholder={provider === "ollama" ? "llama3.2" : "模型名称"} />
          </label>
          <label>
            Base URL
            <input value={baseUrl} onChange={(event) => setBaseUrl(event.target.value)} placeholder={provider === "ollama" ? "http://127.0.0.1:11434" : "可选"} />
          </label>
          <label>
            API key
            <input value={apiKey} onChange={(event) => setApiKey(event.target.value)} type="password" placeholder="只发送到服务端保存" />
          </label>
        </div>
        <label className="checkbox-line">
          <input type="checkbox" checked={allowLocal} disabled={provider !== "ollama"} onChange={(event) => setAllowLocal(event.target.checked)} />
          Ollama 允许本地地址
        </label>
        {disabledByPrivacy ? <p className="workbench-message is-warning">当前项目未授权远程模型，请先在项目设置中开启。</p> : null}
        <button type="submit" disabled={busy || disabledByPrivacy || !model.trim()}>
          保存 Provider
        </button>
      </form>

      <div className="provider-config-list">
        {configs.map((config) => (
          <article key={config.id}>
            <span className={`proposal-status status-${config.verification_status}`}>{config.verification_status}</span>
            <strong>{config.provider} · {config.model}</strong>
            <p>{config.base_url || "默认 Provider 地址"} · {config.has_api_key ? "已保存 API key" : "未保存 API key"}</p>
            {config.verification_message ? <small>{config.verification_message}</small> : null}
            <div>
              <button type="button" disabled={busy} onClick={() => void onVerify(config.id)}>
                验证
              </button>
              <button type="button" disabled={busy} onClick={() => void onDelete(config.id)}>
                删除
              </button>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
