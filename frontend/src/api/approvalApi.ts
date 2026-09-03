import { apiRequest } from "./client";
import type { ApprovalPayload, TaskResponse } from "../types/security";

export function resolveApproval(
  approvalId: string,
  payload: ApprovalPayload,
): Promise<TaskResponse> {
  return apiRequest<TaskResponse>(
    `/approvals/${encodeURIComponent(approvalId)}`,
    { method: "POST", body: JSON.stringify(payload) },
  );
}
