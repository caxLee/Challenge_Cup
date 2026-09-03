import type { RiskLevel } from "../types/security";

export function RiskBadge({ level }: { level: RiskLevel | undefined }) {
  return <span className={`risk-badge risk-${level ?? "unknown"}`}>{level ?? "—"}</span>;
}
