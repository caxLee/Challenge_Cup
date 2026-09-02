"""Risk-routed approvals using the FIDES approval content protocol."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

from agent_framework import Content

from core import CanonicalSecurityEvent, Disposition, RiskAssessment


@dataclass(frozen=True, slots=True)
class ApprovalResult:
    approved: bool
    reason: str


@dataclass(frozen=True, slots=True)
class _Pending:
    signature: str
    requester: str
    disposition: Disposition
    expires_at: datetime


class FidesApprovalAdapter:
    """Bind one approval to one user, session, tool and argument set."""

    def __init__(self, ttl: timedelta = timedelta(minutes=10)) -> None:
        self.ttl = ttl
        self._pending: dict[str, _Pending] = {}
        self.audit_log: list[dict[str, Any]] = []

    @staticmethod
    def _signature(event: CanonicalSecurityEvent, assessment: RiskAssessment) -> str:
        body = {
            "session": event.session_id,
            "principal": event.principal.get("id", ""),
            "tool": event.tool_name,
            "arguments": event.arguments,
            "level": assessment.level.value,
        }
        encoded = json.dumps(body, sort_keys=True, default=str, separators=(",", ":"))
        return hashlib.sha256(encoded.encode()).hexdigest()

    def request(
        self, event: CanonicalSecurityEvent, assessment: RiskAssessment
    ) -> Content:
        if assessment.disposition not in {Disposition.CONFIRM, Disposition.APPROVE}:
            raise ValueError("Only L2/L3 decisions can create approval requests")
        call_id = uuid4().hex
        function_call = Content.from_function_call(
            call_id=call_id, name=event.tool_name, arguments=event.arguments
        )
        self._pending[call_id] = _Pending(
            signature=self._signature(event, assessment),
            requester=str(event.principal.get("id", "")),
            disposition=assessment.disposition,
            expires_at=datetime.now(UTC) + self.ttl,
        )
        request = Content.from_function_approval_request(
            id=call_id,
            function_call=function_call,
            additional_properties={
                "risk_level": assessment.level.value,
                "reasons": list(assessment.reasons),
                "approval_kind": assessment.disposition.value,
            },
        )
        self.audit_log.append({"event": "requested", "call_id": call_id})
        return request

    def resolve(
        self,
        event: CanonicalSecurityEvent,
        assessment: RiskAssessment,
        response: Content,
        *,
        approver: dict[str, Any],
    ) -> ApprovalResult:
        call_id = str(getattr(response, "id", ""))
        pending = self._pending.pop(call_id, None)
        function_call = getattr(response, "function_call", None)
        response_matches = (
            getattr(function_call, "call_id", None) == call_id
            and getattr(function_call, "name", None) == event.tool_name
            and (function_call.parse_arguments() if function_call is not None else None)
            == event.arguments
        )
        reason = "approval_not_pending"
        approved = False
        if pending is not None and datetime.now(UTC) > pending.expires_at:
            reason = "approval_expired"
        elif pending is not None and pending.signature != self._signature(event, assessment):
            reason = "approval_binding_mismatch"
        elif pending is not None and response.type != "function_approval_response":
            reason = "invalid_response"
        elif pending is not None and not response_matches:
            reason = "approval_response_mismatch"
        elif pending is not None and response.approved is not True:
            reason = "approval_rejected"
        elif pending is not None and pending.disposition is Disposition.CONFIRM:
            approved = str(approver.get("id", "")) == pending.requester
            reason = "confirmed" if approved else "requester_identity_mismatch"
        elif pending is not None:
            approved = (
                approver.get("role") in {"approver", "admin"}
                and str(approver.get("id", "")) != pending.requester
            )
            reason = "approved" if approved else "independent_approver_required"
        self.audit_log.append({
            "event": "resolved", "call_id": call_id, "approved": approved,
            "reason": reason, "approver": approver.get("id", ""),
        })
        return ApprovalResult(approved=approved, reason=reason)
