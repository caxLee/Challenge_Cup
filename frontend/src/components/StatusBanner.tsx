import type { TaskResponse } from "../types/security";
import { RiskBadge } from "./RiskBadge";

const labels: Record<TaskResponse["status"], string> = {
  created: "请求已创建", completed: "请求已完成", waiting_confirmation: "等待请求本人确认", waiting_approval: "等待独立审批", rejected: "请求已拒绝", blocked: "请求已阻断",
};

export function StatusBanner({ task }: { task: TaskResponse | null }) {
  if (!task) return <div className="status-banner neutral">选择左侧场景并提交请求</div>;
  return <div className={`status-banner status-${task.status}`}><div><strong>{labels[task.status]}</strong><span>{task.error ?? (task.status === "blocked" ? "该请求不会执行，也没有审批单。" : "后端已返回风险与处理结果。")}</span></div><RiskBadge level={task.risk.level} /></div>;
}
