import { apiRequest } from "./client";
import type { AuditRecord } from "../types/security";

export function getAuditRecords(): Promise<AuditRecord[]> {
  return apiRequest<AuditRecord[]>("/audit");
}
