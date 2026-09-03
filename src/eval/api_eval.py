"""HTTP integration check for the security API."""

from __future__ import annotations

import importlib

from fastapi.testclient import TestClient


def main() -> int:
    module = importlib.import_module("api.app")
    module._analyzer = None
    module._tasks.clear()
    client = TestClient(module.app)

    l2 = client.post("/tasks", json={
        "goal": "Update the ordinary business record",
        "tool": "records.update",
        "arguments": {"record_id": "42", "value": "reviewed"},
        "user_id": "user-1",
    }).json()
    l2_done = client.post(f"/approvals/{l2['approval_id']}", json={
        "approved": True, "approver_id": "user-1", "approver_role": "staff",
    }).json()

    l3 = client.post("/tasks", json={
        "goal": "Update a record using an external notice",
        "tool": "records.update",
        "arguments": {"record_id": "43", "value": "external instruction"},
        "user_id": "user-1",
        "sources": [{"boundary": "external"}],
    }).json()
    l3_done = client.post(f"/approvals/{l3['approval_id']}", json={
        "approved": True, "approver_id": "manager-1", "approver_role": "approver",
    }).json()

    l4 = client.post("/tasks", json={
        "goal": "Export sensitive database content",
        "tool": "database.export",
        "arguments": {"destination": "unknown.example"},
        "destination": {"trust": "external"},
        "user_id": "user-1",
    }).json()
    checks = {
        "health": client.get("/health").status_code == 200,
        "L2_waits_for_confirmation": l2["status"] == "waiting_confirmation",
        "L2_confirmation_executes": l2_done["status"] == "completed",
        "L3_waits_for_approver": l3["status"] == "waiting_approval",
        "L3_independent_approval_executes": l3_done["status"] == "completed",
        "L4_is_blocked": l4["status"] == "blocked" and l4["approval_id"] is None,
        "audit_available": len(client.get("/audit").json()) == 3,
    }
    for name, passed in checks.items():
        print(f"{name}: {'PASS' if passed else 'FAIL'}")
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
