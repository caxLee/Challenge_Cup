import { apiRequest } from "./client";

export interface HealthResponse {
  status: string;
  semantic_analyzer: boolean;
}

export function getHealth(): Promise<HealthResponse> {
  return apiRequest<HealthResponse>("/health");
}
