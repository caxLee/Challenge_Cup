from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from importlib import import_module

app_module = import_module("api.app")


@pytest.fixture()
def client() -> TestClient:
    app_module._analyzer = None
    app_module._tasks.clear()
    return TestClient(app_module.app)


def create(client: TestClient, tool: str, arguments: dict, **extra: object) -> dict:
    payload = {
        "goal": f"Demo request for {tool}",
        "tool": tool,
        "arguments": arguments,
        "user_id": "user-1",
    }
    payload.update(extra)
    response = client.post("/tasks", json=payload)
    assert response.status_code == 200
    return response.json()


def test_l0_completes(client: TestClient) -> None:
    task = create(client, "knowledge.search", {"query": "public"})
    assert task["status"] == "completed"
    assert task["risk"]["level"] == "L0"
    assert task["approval"] == {
        "required": False, "approval_id": None, "kind": None,
        "required_approver": None,
    }
    assert {"request", "risk", "approval", "result", "error"} <= task.keys()


def test_l1_completes_and_is_audited(client: TestClient) -> None:
    task = create(client, "knowledge.internal_search", {"query": "internal"})
    assert task["status"] == "completed"
    assert task["risk"]["level"] == "L1"
    assert task["approval"]["required"] is False
    events = client.get(f"/tasks/{task['task_id']}/events").json()
    assert any(event["event"] == "risk_assessed" for event in events)
    assert all({"timestamp", "status", "risk_level", "disposition", "event", "message", "error"} <= event.keys() for event in events)
    assert client.get("/audit").json()[0]["tool"] == "knowledge.internal_search"


def test_l2_requester_confirmation_and_identity_check(client: TestClient) -> None:
    task = create(client, "records.update", {"record_id": "42", "value": "ok"})
    approval_id = task["approval"]["approval_id"]
    assert task["status"] == "waiting_confirmation"
    assert task["risk"]["disposition"] == "confirm"
    assert task["approval"]["required_approver"] == "requester"
    denied = client.post(f"/approvals/{approval_id}", json={
        "approved": True, "approver_id": "other", "approver_role": "staff",
    })
    assert denied.status_code == 400
    completed = client.post(f"/approvals/{approval_id}", json={
        "approved": True, "approver_id": "user-1", "approver_role": "staff",
    }).json()
    assert completed["status"] == "completed"
    assert completed["approval"] == {
        "required": False, "approval_id": None, "kind": None,
        "required_approver": None,
    }
    assert [event["event"] for event in client.get(f"/tasks/{task['task_id']}/events").json()] == [
        "created", "risk_assessed", "approval_requested", "risk_assessed",
        "approval_resolved", "completed",
    ]


def test_l2_requester_can_reject(client: TestClient) -> None:
    task = create(client, "records.update", {"record_id": "43", "value": "no"})
    response = client.post(f"/approvals/{task['approval']['approval_id']}", json={
        "approved": False, "approver_id": "user-1", "approver_role": "staff",
    })
    body = response.json()
    assert body["status"] == "rejected"
    assert body["approval"] == {
        "required": False, "approval_id": None, "kind": None,
        "required_approver": None,
    }


def test_l2_non_staff_cannot_confirm(client: TestClient) -> None:
    task = create(client, "records.update", {"record_id": "44"})
    response = client.post(f"/approvals/{task['approval']['approval_id']}", json={
        "approved": True, "approver_id": "user-1", "approver_role": "admin",
    })
    assert response.status_code == 400


def test_l3_requires_independent_approver(client: TestClient) -> None:
    task = create(client, "shell.execute", {"command": "echo demo"})
    approval_id = task["approval"]["approval_id"]
    assert task["status"] == "waiting_approval"
    assert task["risk"]["level"] == "L3"
    assert task["approval"]["required_approver"] == "independent_approver"
    self_approval = client.post(f"/approvals/{approval_id}", json={
        "approved": True, "approver_id": "user-1", "approver_role": "approver",
    })
    assert self_approval.status_code == 400
    bad_role = client.post(f"/approvals/{approval_id}", json={
        "approved": True, "approver_id": "manager-1", "approver_role": "staff",
    })
    assert bad_role.status_code == 400
    completed = client.post(f"/approvals/{approval_id}", json={
        "approved": True, "approver_id": "manager-1", "approver_role": "admin",
    }).json()
    assert completed["status"] == "completed"
    assert completed["approval"]["required"] is False
    assert client.post(f"/approvals/{approval_id}", json={
        "approved": True, "approver_id": "manager-1", "approver_role": "admin",
    }).status_code == 404


def test_l3_admin_can_approve(client: TestClient) -> None:
    task = create(client, "shell.execute", {"command": "echo admin"})
    response = client.post(f"/approvals/{task['approval']['approval_id']}", json={
        "approved": True, "approver_id": "admin-1", "approver_role": "admin",
    })
    assert response.json()["status"] == "completed"


def test_l4_is_blocked_without_approval(client: TestClient) -> None:
    task = create(
        client, "database.export", {"destination": "outside.example"},
        destination={"trust": "external"},
    )
    assert task["status"] == "blocked"
    assert task["risk"]["level"] == "L4"
    assert task["approval"]["required"] is False
    assert task["approval"]["approval_id"] is None
    assert client.post("/approvals/never-created", json={
        "approved": True, "approver_id": "admin-1", "approver_role": "admin",
    }).status_code == 404


def test_missing_resources_and_unknown_tool(client: TestClient) -> None:
    assert client.get("/tasks/missing").status_code == 404
    assert client.post("/approvals/missing", json={
        "approved": True, "approver_id": "user-1", "approver_role": "staff",
    }).status_code == 404
    unknown = client.post("/tasks", json={
        "goal": "unknown", "tool": "missing.tool", "arguments": {}, "user_id": "user-1",
    })
    assert unknown.status_code == 400
