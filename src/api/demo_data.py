"""Load real attack cases as safe, executable API demo requests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


_ATTACKS_DIR = Path(__file__).resolve().parents[2] / "datasets" / "raw" / "attacks"


def _safe_tool(case: dict[str, Any]) -> tuple[str, dict[str, Any], dict[str, Any]]:
    text = " ".join(
        str(case.get(key, ""))
        for key in ("Attacker Instruction", "Description", "Attack goal", "Attack Type")
    ).lower()
    if any(word in text for word in ("exfiltrat", "external", "outside", "leak", "credential")):
        return (
            "database.export",
            {"destination": "external-demo.example"},
            {"trust": "external"},
        )
    if any(word in text for word in ("command", "execute", "delete", "destroy", "bypass", "privilege")):
        return "shell.execute", {"command": "echo security-demo"}, {}
    if any(word in text for word in ("read", "search", "review", "query", "retrieve")):
        return "knowledge.internal_search", {"query": case.get("Attacker Instruction", "")[:120]}, {}
    return "records.update", {"record_id": "real-case-demo", "value": case.get("Attacker Instruction", "")}, {}


def load_demo_requests() -> list[dict[str, Any]]:
    requests: list[dict[str, Any]] = []
    for path in sorted(_ATTACKS_DIR.glob("*.jsonl")):
        category = path.stem
        with path.open(encoding="utf-8") as stream:
            for index, line in enumerate(stream):
                case = json.loads(line)
                tool, arguments, destination = _safe_tool(case)
                case_id = f"attack-{category}-{index}"
                instruction = str(case.get("Attacker Instruction", ""))
                requests.append({
                    "id": case_id,
                    "title": str(case.get("Attacker Tool", case_id)),
                    "description": instruction,
                    "source": "datasets/raw/attacks/" + path.name,
                    "raw_case": case,
                    "expected_level": "L4" if tool == "database.export" else "L3" if tool == "shell.execute" else "L2" if tool == "records.update" else "L1",
                    "payload": {
                        "goal": instruction,
                        "tool": tool,
                        "arguments": arguments,
                        "user_id": "demo-user",
                        "user_role": "staff",
                        "sources": [{"boundary": "user", "case_id": case_id}],
                        "observations": [
                            str(case.get("Description", "")),
                            str(case.get("Attack goal", "")),
                        ],
                        "destination": destination,
                        "authorized": True,
                        "case_id": case_id,
                        "case_title": str(case.get("Attacker Tool", case_id)),
                        "case_source": "datasets/raw/attacks/" + path.name,
                    },
                })
    return requests
