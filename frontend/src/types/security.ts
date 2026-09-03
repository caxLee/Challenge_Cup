export type RiskLevel = "L0" | "L1" | "L2" | "L3" | "L4";

export type TaskStatus =
  | "created"
  | "completed"
  | "waiting_confirmation"
  | "waiting_approval"
  | "rejected"
  | "blocked";

export type Disposition = "allow" | "audit" | "confirm" | "approve" | "block";
export type ApproverRole = "staff" | "approver" | "admin";

export interface TaskRequest {
  goal: string;
  tool: string;
  arguments: Record<string, unknown>;
  user_id: string;
  user_role: string;
  sources?: Array<Record<string, unknown>>;
  observations?: string[];
  destination?: Record<string, unknown>;
  authorized?: boolean;
  case_id?: string;
  case_title?: string;
  case_source?: string;
}

export interface DemoRequest {
  id: string;
  title: string;
  description: string;
  source: string;
  raw_case: Record<string, unknown>;
  expected_level: RiskLevel;
  payload: TaskRequest;
}

export interface RiskAssessment {
  level: RiskLevel;
  disposition: Disposition;
  reasons: string[];
  rules: string[];
  semantic?: {
    signals: string[];
    confidence: number;
    evidence: string[];
    error: string | null;
  };
}

export interface ApprovalInfo {
  required: boolean;
  approval_id: string | null;
  kind: "confirm" | "approve" | null;
  required_approver: "requester" | "independent_approver" | null;
}

export interface TaskResponse {
  task_id: string;
  status: TaskStatus;
  request: TaskRequest;
  risk: RiskAssessment;
  approval: ApprovalInfo;
  approval_id?: string | null;
  result: unknown;
  error: string | null;
}

export interface ApprovalPayload {
  approved: boolean;
  approver_id: string;
  approver_role: ApproverRole;
}

export interface TaskEvent {
  timestamp: string;
  status: TaskStatus;
  risk_level: RiskLevel;
  disposition: Disposition;
  event:
    | "created"
    | "risk_assessed"
    | "approval_requested"
    | "approval_resolved"
    | "completed"
    | "rejected"
    | "blocked";
  message: string;
  error: string | null;
}

export interface AuditRecord {
  task_id: string;
  user_id: string;
  tool: string;
  case_title?: string | null;
  case_source?: string | null;
  risk_level: RiskLevel | null;
  status: TaskStatus;
  events: TaskEvent[];
  approval_audit_log: Array<Record<string, unknown>>;
  approvals?: Array<Record<string, unknown>>;
}
