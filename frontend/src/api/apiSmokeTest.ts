import { getAuditRecords } from "./auditApi";
import { resolveApproval } from "./approvalApi";
import { createTask, getTask, getTaskEvents } from "./taskApi";
import { demoRequests } from "../mock/demoRequests";

export async function runApiSmokeTest(): Promise<void> {
  const task = await createTask(demoRequests[2].payload);
  const loadedTask = await getTask(task.task_id);
  const events = await getTaskEvents(task.task_id);
  if (loadedTask.task_id !== task.task_id || events.length === 0) {
    throw new Error("Task API smoke test failed");
  }

  if (task.approval.approval_id) {
    await resolveApproval(task.approval.approval_id, {
      approved: false,
      approver_id: task.request.user_id,
      approver_role: "staff",
    });
  }
  await getAuditRecords();

  let errorObserved = false;
  try {
    await getTask("missing/task?id=1");
  } catch (reason) {
    errorObserved = reason instanceof Error && reason.message.includes("HTTP");
  }
  if (!errorObserved) throw new Error("HTTP error smoke test failed");
}
