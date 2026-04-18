import type { ProviderConfigRecord, ThesisProject } from "../app/api";

type ModelStatusBadgeProps = {
  project: ThesisProject | null;
  configs: ProviderConfigRecord[];
};

export function ModelStatusBadge({ project, configs }: ModelStatusBadgeProps) {
  const remoteAllowed = project?.remote_provider_allowed ?? false;
  const verifiedConfigs = configs.filter((item) => item.verification_status === "verified");
  if (!remoteAllowed) {
    return <span className="model-status model-status-local">本地模式</span>;
  }
  if (verifiedConfigs.length > 0) {
    return <span className="model-status model-status-ready">远程已授权 · {verifiedConfigs[0].provider}</span>;
  }
  return <span className="model-status model-status-warn">远程已授权 · Provider 待验证</span>;
}
