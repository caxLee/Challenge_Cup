import { apiRequest } from "./client";
import type { DemoRequest, TaskEvent, TaskRequest, TaskResponse } from "../types/security";

export function getDemoRequests(): Promise<DemoRequest[]> {
  return apiRequest<DemoRequest[]>("/demo/requests");
}

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
