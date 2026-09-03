import { apiRequest } from "./client";
import type { TaskEvent, TaskRequest, TaskResponse } from "../types/security";

export function createTask(payload: TaskRequest): Promise<TaskResponse> {
  return apiRequest<TaskResponse>("/tasks", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getTask(taskId: string): Promise<TaskResponse> {
  return apiRequest<TaskResponse>(`/tasks/${encodeURIComponent(taskId)}`);
}

export function getTaskEvents(taskId: string): Promise<TaskEvent[]> {
  return apiRequest<TaskEvent[]>(
    `/tasks/${encodeURIComponent(taskId)}/events`,
  );
}
