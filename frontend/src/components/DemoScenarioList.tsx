import { useState } from "react";
import type { DemoRequest, RiskLevel } from "../types/security";
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
  const levels: RiskLevel[] = ["L0", "L1", "L2", "L3", "L4"];
  const [modalLevel, setModalLevel] = useState<RiskLevel | null>(null);
  const modalCases = modalLevel === null ? [] : demos
    .map((demo, index) => ({ demo, index }))
    .filter(item => item.demo.expected_level === modalLevel);
  const selectedCase = selected === null ? null : demos[selected];

  return (
    <section className="panel scenario-panel">
      <div className="panel-heading"><span>风险类型</span><span className="muted">5 个等级</span></div>
      <div className="scenario-list">
        {levels.map(level => {
          const count = demos.filter(demo => demo.expected_level === level).length;
          return <button className="scenario-type" key={level} onClick={() => setModalLevel(level)}>
            <RiskBadge level={level} />
            <span className="scenario-copy"><strong>{level} 风险请求</strong><small>{count} 条真实案例</small></span>
          </button>;
        })}
      </div>
      <p className="hint">点击风险类型，在弹窗中选择真实案例并提交；最终风险等级以 API 返回为准。</p>
      {modalLevel !== null && <div className="modal-backdrop" role="presentation" onClick={() => setModalLevel(null)}>
        <div className="scenario-modal" role="dialog" aria-modal="true" aria-labelledby="scenario-modal-title" onClick={event => event.stopPropagation()}>
          <div className="modal-header"><div><span className="eyebrow">REAL DATASET CASES</span><h2 id="scenario-modal-title"><RiskBadge level={modalLevel} /> 选择 {modalLevel} 案例</h2></div><button className="modal-close" onClick={() => setModalLevel(null)} aria-label="关闭">×</button></div>
          <div className="modal-body">
            {modalCases.length === 0 ? <p className="scenario-empty">暂无该等级案例</p> : <div className="modal-case-list">{modalCases.map(({ demo, index }) => <button className={`modal-case ${selected === index ? "selected" : ""}`} key={demo.id} onClick={() => onSelect(index)}><strong>{demo.title}</strong><small>{demo.description}</small><small className="scenario-source">{demo.source}</small></button>)}</div>}
            {selectedCase && selectedCase.expected_level === modalLevel && <div className="selected-case"><strong>已选择</strong><span>{selectedCase.title}</span><small>{selectedCase.description}</small></div>}
          </div>
          <div className="modal-footer"><button className="button secondary" onClick={() => setModalLevel(null)}>取消</button><button className="button primary" disabled={selected === null || !selectedCase || selectedCase.expected_level !== modalLevel || loading || submitted} onClick={() => { setModalLevel(null); onSubmit(); }}>{loading ? "正在评估…" : submitted ? "请求已提交" : "提交请求"}</button></div>
        </div>
      </div>}
    </section>
  );
}
