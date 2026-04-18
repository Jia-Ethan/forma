import type { ThesisProject } from "../app/api";

type PrivacyConsentBannerProps = {
  project: ThesisProject | null;
};

export function PrivacyConsentBanner({ project }: PrivacyConsentBannerProps) {
  if (!project) return null;
  const remoteAllowed = project.remote_provider_allowed && project.privacy_mode === "remote_allowed";
  return (
    <section className={remoteAllowed ? "privacy-banner privacy-banner-remote" : "privacy-banner"}>
      <strong>{remoteAllowed ? "远程模型已授权" : "本地优先模式"}</strong>
      <p>
        {remoteAllowed
          ? "该项目允许把经用户确认的任务内容发送到已配置 Provider。密钥仍只保存在服务端，前端不会读取。"
          : "默认不会把真实论文内容发送到远程模型。需要远程协作时，请先在项目设置中显式授权。"}
      </p>
    </section>
  );
}
