import { useEffect, useState } from "react";
import { resolveApproval } from "../api";
import type { ApproverRole, TaskResponse } from "../types/security";

interface Props { task: TaskResponse | null; onResolved: (task: TaskResponse) => Promise<void>; }

export function ApprovalPanel({ task, onResolved }: Props) {
  const [approverId, setApproverId] = useState("manager-1");
  const [approverRole, setApproverRole] = useState<ApproverRole>("approver");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const waiting = task?.status === "waiting_confirmation" || task?.status === "waiting_approval";
  const l2 = task?.status === "waiting_confirmation";
  const hasApproval = Boolean(task?.approval.approval_id);

  useEffect(() => { setError(null); setLoading(false); }, [task?.task_id, task?.status, task?.approval.approval_id]);

  if (!task) return <section className="panel approval-panel empty-card">提交请求后查看审批区域。</section>;
  if (task.status === "blocked") return <section className="panel approval-panel blocked-card"><div className="panel-heading">审批区域</div><strong>L4 请求已阻断</strong><p>此请求没有审批单，不能通过审批接口执行。</p><ul>{task.risk.reasons.map(reason => <li key={reason}>{reason}</li>)}</ul></section>;
  if (!waiting) return <section className="panel approval-panel"><div className="panel-heading">审批区域</div><strong>{task.status === "rejected" ? "审批已拒绝" : "无需待处理审批"}</strong><p>{task.error ?? "当前任务已经结束。"}</p></section>;

  const submit = async (approved: boolean) => {
    if (!task.approval.approval_id) return;
    setLoading(true); setError(null);
    try {
      const next = await resolveApproval(task.approval.approval_id, { approved, approver_id: l2 ? task.request.user_id : approverId, approver_role: l2 ? "staff" : approverRole });
      await onResolved(next);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "审批请求失败");
    } finally { setLoading(false); }
  };

  return <section className="panel approval-panel"><div className="panel-heading">审批区域</div><div className="approval-callout"><strong>{l2 ? "等待请求本人确认" : "等待独立审批"}</strong><span>要求：{l2 ? "请求本人" : "独立 approver 或 admin"}</span></div>{!hasApproval && <div className="inline-error">当前没有可处理的审批单</div>}{!l2 && <div className="form-grid"><label>审批人 ID<input value={approverId} onChange={event => setApproverId(event.target.value)} disabled={!hasApproval || loading} /></label><label>审批人角色<select value={approverRole} onChange={event => setApproverRole(event.target.value as ApproverRole)} disabled={!hasApproval || loading}><option value="approver">approver</option><option value="admin">admin</option></select></label></div>}{error && <div className="inline-error">{error}</div>}<div className="approval-actions"><button className="button danger" disabled={loading || !hasApproval} onClick={() => submit(false)}>拒绝</button><button className="button primary" disabled={loading || !hasApproval} onClick={() => submit(true)}>{loading ? "提交中…" : l2 ? "确认执行" : "批准执行"}</button></div></section>;
}
