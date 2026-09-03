import { useState } from "react";
import type { AuditRecord } from "../types/security";
import { RiskBadge } from "./RiskBadge";

interface Props { records: AuditRecord[]; loading: boolean; error: string | null; }

export function AuditPanel({ records, loading, error }: Props) {
  const [open, setOpen] = useState<string | null>(null);
  return <section className="panel audit-panel"><div className="panel-heading">审计记录 <span className="muted">{records.length}</span></div>{loading && <p className="muted">正在加载审计记录…</p>}{error && <div className="inline-error"><strong>审计加载失败</strong><br />{error}</div>}{!loading && !error && records.length === 0 && <p className="muted">提交请求后查看审计记录。</p>}{records.map(record => <div className="audit-record" key={record.task_id}><button onClick={() => setOpen(open === record.task_id ? null : record.task_id)}><span><RiskBadge level={record.risk_level ?? undefined} /><strong>{record.tool}</strong></span><span>{record.status}　›</span></button>{open === record.task_id && <div className="audit-details"><p>task_id：<span className="mono">{record.task_id}</span></p><p>用户：{record.user_id}</p><p>审批审计：{record.approval_audit_log.length} 条</p><pre>{JSON.stringify(record.approval_audit_log, null, 2)}</pre></div>}</div>)}</section>;
}
