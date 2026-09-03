import type { RiskAssessment } from "../types/security";
import { RiskBadge } from "./RiskBadge";

export function RiskAssessmentCard({ risk }: { risk: RiskAssessment | undefined }) {
  if (!risk) return <section className="panel empty-card">风险评估将在提交请求后显示。</section>;
  return (
    <section className="panel">
      <div className="panel-heading">风险评估</div>
      <div className="risk-summary"><RiskBadge level={risk.level} /><div><strong>{risk.disposition}</strong><small>后端真实处置结果</small></div></div>
      <List title="风险原因" values={risk.reasons} empty="未返回风险原因" />
      <List title="命中规则" values={risk.rules} empty="未命中显式规则" />
      {risk.semantic && <div className="semantic"><label>语义分析</label><p>signals：{risk.semantic.signals.join(", ") || "无"}</p><p>confidence：{risk.semantic.confidence}</p><p>evidence：{risk.semantic.evidence.join(", ") || "无"}</p></div>}
    </section>
  );
}

function List({ title, values, empty }: { title: string; values: string[]; empty: string }) {
  return <div className="tag-section"><label>{title}</label><div className="tag-list">{values.length ? values.map(value => <span className="tag" key={value}>{value}</span>) : <span className="muted">{empty}</span>}</div></div>;
}
