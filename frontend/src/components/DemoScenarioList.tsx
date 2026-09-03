import type { DemoRequest } from "../mock/demoRequests";
import { RiskBadge } from "./RiskBadge";

interface Props {
  demos: DemoRequest[];
  selected: number | null;
  submitted: boolean;
  loading: boolean;
  onSelect: (index: number) => void;
  onSubmit: () => void;
}

export function DemoScenarioList({ demos, selected, submitted, loading, onSelect, onSubmit }: Props) {
  return (
    <section className="panel scenario-panel">
      <div className="panel-heading"><span>演示请求</span><span className="muted">{demos.length} 个场景</span></div>
      <div className="scenario-list">
        {demos.map((demo, index) => (
          <button className={`scenario ${selected === index ? "selected" : ""}`} key={demo.payload.tool} onClick={() => onSelect(index)}>
            <RiskBadge level={demo.expectedLevel} />
            <span className="scenario-copy"><strong>{demo.title}</strong><small>{demo.description}</small></span>
            <span className="chevron">›</span>
          </button>
        ))}
      </div>
      <button className="button primary full" disabled={selected === null || loading || submitted} onClick={onSubmit}>
        {loading ? "正在评估…" : submitted ? "请求已提交" : "提交请求"}
      </button>
      <p className="hint">预期等级仅用于场景说明，最终结果以 API 返回为准。</p>
    </section>
  );
}
