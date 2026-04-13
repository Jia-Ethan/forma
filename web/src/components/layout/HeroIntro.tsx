import type { HealthResponse } from "../../generated/contracts";
import { formatBytes } from "../../app/domain";
import { CapabilitySummary } from "../../features/health/CapabilitySummary";
import { SectionCard, StatusBadge } from "../ui";

type HeroIntroProps = {
  health: HealthResponse | null;
};

export function HeroIntro({ health }: HeroIntroProps) {
  return (
    <section className="hero-intro" aria-labelledby="hero-title">
      <div className="hero-copy">
        <p className="eyebrow">SCNU Thesis Portal v0.2</p>
        <h1 id="hero-title">把论文内容整理成可校对、可导出的学术工作台。</h1>
        <p className="hero-lede">
          上传 <code>.docx</code> 或粘贴正文，识别结构后在网页里 review，再导出 <code>.tex</code> 工程 zip。
        </p>

        <div className="hero-route-grid" aria-label="输入入口">
          <article className="hero-route-card">
            <p className="section-eyebrow">入口 01</p>
            <h2>上传 .docx</h2>
            <p>适合已有论文文档，优先抽取封面字段、摘要、章节和参考文献骨架。</p>
          </article>
          <article className="hero-route-card">
            <p className="section-eyebrow">入口 02</p>
            <h2>粘贴正文</h2>
            <p>适合快速整理论文结构，先得到稳定章节框架，再手动补全元信息。</p>
          </article>
        </div>

        <div className="hero-inline-note" role="note">
          <StatusBadge tone="info">当前输出：.tex 工程 zip</StatusBadge>
          <p>不是线上直接 PDF。生产环境默认关闭 PDF 编译，建议下载后在本地 TeX 环境继续检查。</p>
        </div>
      </div>

      <SectionCard tone="feature" className="hero-rail">
        <div className="hero-status-top">
          <div>
            <p className="section-eyebrow">先判断是否适合你</p>
            <h2>当前能力、边界与推荐路径</h2>
          </div>
          <StatusBadge tone={health?.ok ? "success" : "info"}>{health?.ok ? "在线" : "加载中"}</StatusBadge>
        </div>

        <div className="hero-rail-group">
          <p className="section-eyebrow">当前能力</p>
          <CapabilitySummary health={health} compact />
        </div>

        <div className="hero-rail-group">
          <p className="section-eyebrow">当前边界</p>
          <ul className="hero-list">
            <li>当前不是学校官方认证工具，不承诺逐条覆盖全部格式细则。</li>
            <li>不会保留 Word 原始样式，也不承诺复杂表格、脚注与图片完整恢复。</li>
            <li>线上主路径是 <code>.tex</code> 工程 zip，PDF 不作为当前稳定能力。</li>
          </ul>
        </div>

        <div className="hero-rail-group">
          <p className="section-eyebrow">推荐路径</p>
          <ol className="hero-list hero-list-ordered">
            <li>先上传现有 `.docx`，或粘贴正文得到结构骨架。</li>
            <li>在 review 工作台里补齐封面字段、摘要、章节和参考文献。</li>
            <li>导出 `.tex` 工程 zip，再在本地编译和做最终格式核查。</li>
          </ol>
        </div>

        <p className="hero-status-footnote">上传上限：{formatBytes(health?.limits.max_docx_size_bytes)}</p>
      </SectionCard>
    </section>
  );
}
