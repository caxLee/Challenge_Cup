from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel


class AttackCase(BaseModel):
    case_id: str
    category: str
    attacker_tool: str
    attacker_instruction: str
    description: str
    attack_goal: str
    attack_type: str
    corresponding_agent: str
    aggressive: bool


def load_attack_cases(root: Path | None = None) -> list[AttackCase]:
    data_root = root or Path(__file__).resolve().parents[2] / "datasets" / "raw" / "attacks"
    cases: list[AttackCase] = []
    for path in sorted(data_root.glob("*.jsonl")):
        with path.open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                raw = json.loads(line)
                cases.append(
                    AttackCase(
                        case_id=f"{path.stem}-{line_number:04d}",
                        category=path.stem,
                        attacker_tool=raw["Attacker Tool"],
                        attacker_instruction=raw["Attacker Instruction"],
                        description=raw["Description"],
                        attack_goal=raw["Attack goal"],
                        attack_type=raw["Attack Type"],
                        corresponding_agent=raw["Corresponding Agent"],
                        aggressive=str(raw["Aggressive"]).strip().lower() == "true",
                    )
                )
    return cases
