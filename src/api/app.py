"""Minimal HTTP API for task risk routing and approval."""

from __future__ import annotations

import os
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, Any
from uuid import uuid4

from agent_framework import Content, FunctionTool
from agent_framework.security import SecureAgentConfig
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from pydantic import BaseModel, Field

from adapters import FidesRuntimeAdapter, ModelRiskAnalyzer
from core import ExecutionContext, ToolManifest
from api.demo_data import load_demo_requests
from eval.runtime import Depends, TaskEnvironment, make_function


class RuntimeState(TaskEnvironment):
    knowledge: dict[str, str] = Field(default_factory=dict)
    records: dict[str, Any] = Field(default_factory=dict)
    exports: list[dict[str, Any]] = Field(default_factory=list)
    commands: list[str] = Field(default_factory=list)


def knowledge_search(
    environment: Annotated[RuntimeState, Depends(lambda value: value)], query: str
) -> dict[str, str | None]:
    return {"query": query, "result": environment.knowledge.get(query)}


def knowledge_internal_search(
    environment: Annotated[RuntimeState, Depends(lambda value: value)], query: str
) -> dict[str, str | None]:
    return {"query": query, "result": environment.knowledge.get(query)}


def records_update(
    environment: Annotated[RuntimeState, Depends(lambda value: value)],
    record_id: str,
    value: Any = None,
) -> str:
    environment.records[record_id] = value
    return "updated"


def database_export(
    environment: Annotated[RuntimeState, Depends(lambda value: value)],
    destination: str,
) -> str:
    environment.exports.append({"destination": destination})
    return "exported"


def shell_execute(
    environment: Annotated[RuntimeState, Depends(lambda value: value)],
    command: str,
) -> str:
    environment.commands.append(command)
    return "executed"


def _functions():
    functions = []
    for name, function in {
        "knowledge.search": knowledge_search,
        "knowledge.internal_search": knowledge_internal_search,
        "records.update": records_update,
        "database.export": database_export,
        "shell.execute": shell_execute,
    }.items():
        item = make_function(function)
        item.name = name
        functions.append(item)
    return functions


class TaskRequest(BaseModel):
    goal: str = Field(min_length=1)
    tool: str = Field(min_length=1)
    arguments: dict[str, Any] = Field(default_factory=dict)
    user_id: str = Field(min_length=1)
    user_role: str = Field(default="staff", min_length=1)
    sources: list[dict[str, Any]] = Field(default_factory=lambda: [{"boundary": "user"}])
    observations: list[str] = Field(default_factory=list)
    destination: dict[str, Any] = Field(default_factory=dict)
    authorized: bool = True
    case_id: str | None = None
    case_title: str | None = None
    case_source: str | None = None


class ApprovalRequest(BaseModel):
    approved: bool
    approver_id: str = Field(min_length=1)
    approver_role: str = Field(default="staff", min_length=1)


@dataclass
class TaskRecord:
    request: TaskRequest
    runtime: FidesRuntimeAdapter
    environment: RuntimeState
    context: ExecutionContext
    status: str = "created"
    risk: dict[str, Any] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)
    approval: Content | None = None
    result: Any = None
    error: str | None = None


load_dotenv()
_manifest = ToolManifest.from_file(Path(__file__).resolve().parents[2] / "config" / "tools.yaml")
_analyzer = None
if os.getenv("MODEL_API_KEY"):
    _analyzer = ModelRiskAnalyzer(
        OpenAI(
            api_key=os.environ["MODEL_API_KEY"],
            base_url=os.getenv("MODEL_BASE_URL", "https://ai.stackway.org/v1"),
            timeout=60.0,
            max_retries=1,
        ),
        os.getenv("MODEL_NAME", "deepseek-v4-flash"),
    )

app = FastAPI(title="Agent Runtime Security API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)
_tasks: dict[str, TaskRecord] = {}


def _view(task_id: str, record: TaskRecord) -> dict[str, Any]:
    approval_id = str(record.approval.id) if record.approval is not None else None
    disposition = record.risk.get("disposition")
    approval_required = record.approval is not None
    approval_kind = disposition if approval_required else None
    required_approver = (
        "requester" if approval_required and disposition == "confirm" else
        "independent_approver" if approval_required and disposition == "approve" else None
    )
    return {
        "task_id": task_id,
        "status": record.status,
        "request": record.request.model_dump(),
        "risk": record.risk,
        "approval": {
            "required": approval_required,
            "approval_id": approval_id,
            "kind": approval_kind,
            "required_approver": required_approver,
        },
        # Kept as a compatibility alias for the original demo client.
        "approval_id": approval_id,
        "result": _jsonable(record.result),
        "error": record.error,
    }


def _jsonable(value: Any) -> Any:
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    return FunctionTool._make_dumpable(value)


def _append_event(record: TaskRecord, event: str, message: str, error: str | None = None) -> None:
    record.events.append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": record.status,
        "risk_level": record.risk.get("level", "L0"),
        "disposition": record.risk.get("disposition", "allow"),
        "event": event,
        "message": message,
        "error": error,
    })


def _execute(record: TaskRecord, response: Content | None = None, approver: dict[str, Any] | None = None) -> None:
    result, error, assessment = record.runtime.run_tool(
        record.environment,
        record.request.tool,
        record.request.arguments,
        record.context,
        approval_response=response,
        approver=approver,
    )
    record.risk = {
        "level": assessment.level.value,
        "disposition": assessment.disposition.value,
        "reasons": list(assessment.reasons),
        "rules": list(assessment.rule_ids),
        "semantic": {
            "signals": list(record.runtime.last_analysis.signals),
            "confidence": record.runtime.last_analysis.confidence,
            "evidence": list(record.runtime.last_analysis.evidence),
            "error": record.runtime.last_analysis.error,
        },
    }
    if response is None and record.runtime.last_analysis.confidence >= record.runtime.semantic_threshold:
        record.context = replace(
            record.context,
            risk_signals=tuple(dict.fromkeys(
                (*record.context.risk_signals, *record.runtime.last_analysis.signals)
            )),
        )
    record.error = error
    _append_event(record, "risk_assessed", "Risk assessment completed", error)
    if isinstance(result, Content) and result.type == "function_approval_request":
        record.approval = result
        record.status = "waiting_confirmation" if assessment.level.value == "L2" else "waiting_approval"
        _append_event(record, "approval_requested", "Approval is required before tool execution")
    elif error:
        record.status = "blocked" if assessment.level.value == "L4" else "rejected"
        if response is not None:
            _append_event(record, "approval_resolved", "Approval was rejected", error)
        _append_event(record, record.status, "Task was blocked" if record.status == "blocked" else "Task was rejected", error)
    else:
        record.result = result
        record.status = "completed"
        if response is not None:
            _append_event(record, "approval_resolved", "Approval was accepted")
        _append_event(record, "completed", "Tool execution completed")


@app.get("/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "semantic_analyzer": _analyzer is not None}


@app.get("/demo/requests")
def demo_requests() -> list[dict[str, Any]]:
    return load_demo_requests()


@app.post("/tasks")
def create_task(request: TaskRequest) -> dict[str, Any]:
    if _manifest.get(request.tool) is None:
        raise HTTPException(400, f"Unknown tool: {request.tool}")
    task_id = uuid4().hex
    context = ExecutionContext(
        framework="security-api",
        session_id=task_id,
        principal={"id": request.user_id, "role": request.user_role},
        task={"goal": request.goal},
        sources=tuple(request.sources),
        observations=tuple(request.observations),
        destination=request.destination,
        authorized=request.authorized,
    )
    record = TaskRecord(
        request=request,
        runtime=FidesRuntimeAdapter(
            _functions(), tool_manifest=_manifest,
            security=SecureAgentConfig(auto_hide_untrusted=False),
            risk_analyzer=_analyzer,
        ),
        environment=RuntimeState(),
        context=context,
    )
    _tasks[task_id] = record
    _append_event(record, "created", "Task created")
    _execute(record)
    return _view(task_id, record)


@app.get("/tasks/{task_id}")
def get_task(task_id: str) -> dict[str, Any]:
    record = _tasks.get(task_id)
    if record is None:
        raise HTTPException(404, "Task not found")
    return _view(task_id, record)


@app.get("/tasks/{task_id}/events")
def get_events(task_id: str) -> list[dict[str, Any]]:
    record = _tasks.get(task_id)
    if record is None:
        raise HTTPException(404, "Task not found")
    return record.events


@app.post("/approvals/{approval_id}")
def resolve_approval(approval_id: str, request: ApprovalRequest) -> dict[str, Any]:
    match = next(
        ((task_id, record) for task_id, record in _tasks.items()
         if record.approval is not None and str(record.approval.id) == approval_id),
        None,
    )
    if match is None:
        raise HTTPException(404, "Approval not found")
    task_id, record = match
    if record.risk.get("level") == "L4":
        raise HTTPException(400, "L4 tasks cannot be approved")
    if record.risk.get("level") == "L2":
        if request.approver_id != record.request.user_id:
            raise HTTPException(400, "L2 confirmation must be performed by the requester")
        if request.approver_role != "staff":
            raise HTTPException(400, "L2 confirmation requires the staff role")
    elif record.risk.get("level") == "L3":
        if request.approver_role not in {"approver", "admin"}:
            raise HTTPException(400, "L3 approval requires approver or admin role")
        if request.approver_id == record.request.user_id:
            raise HTTPException(400, "L3 approval requires an independent approver")
    response = record.approval.to_function_approval_response(request.approved)
    _execute(
        record, response,
        {"id": request.approver_id, "role": request.approver_role},
    )
    record.approval = None
    return _view(task_id, record)


@app.get("/audit")
def audit() -> list[dict[str, Any]]:
    return [
        {
            "task_id": task_id,
            "user_id": record.request.user_id,
            "tool": record.request.tool,
            "case_title": record.request.case_title,
            "case_source": record.request.case_source,
            "risk_level": record.risk.get("level"),
            "status": record.status,
            "events": record.events,
            "approval_audit_log": record.runtime.approvals.audit_log,
            "approvals": record.runtime.approvals.audit_log,
        }
        for task_id, record in _tasks.items()
    ]
