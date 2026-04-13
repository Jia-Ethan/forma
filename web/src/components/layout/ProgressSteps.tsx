import { WorkspaceStep, stepIndex } from "../../app/domain";

const steps = [
  { key: "input", label: "输入内容", description: "上传或粘贴论文文本" },
  { key: "recognizing", label: "结构识别", description: "抽取摘要、章节与参考文献" },
  { key: "review", label: "校对修正", description: "补全字段并检查正文" },
  { key: "export", label: "导出成果", description: "生成 .tex 工程 zip" },
] as const;

type ProgressStepsProps = {
  step: WorkspaceStep;
};

export function ProgressSteps({ step }: ProgressStepsProps) {
  const activeIndex = stepIndex(step);

  return (
    <nav className="progress-shell" aria-label="处理步骤">
      <ol className="progress-steps">
      {steps.map((item, index) => {
        const state = index < activeIndex ? "done" : index === activeIndex ? "current" : "upcoming";
        return (
          <li
            key={item.key}
            className={`progress-step progress-step-${state}`}
            aria-current={state === "current" ? "step" : undefined}
          >
            <span className="progress-step-marker">{index + 1}</span>
            <span className="progress-step-copy">
              <small>阶段 {index + 1}</small>
              <strong>{item.label}</strong>
              <p>{item.description}</p>
            </span>
          </li>
        );
      })}
      </ol>
    </nav>
  );
}
