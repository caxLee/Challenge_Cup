"""Classify attack cases using only runtime-visible provenance and tool capability."""

from __future__ import annotations

import argparse
from collections import Counter

from core import ExecutionContext
from .cases import load_attack_cases
from .model_eval import TOOL_MANIFEST
from core import EventBuilder, RuleRiskEngine


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()
    builder = EventBuilder(TOOL_MANIFEST)
    engine = RuleRiskEngine()
    results = []
    for case in load_attack_cases()[:args.limit]:
        context = ExecutionContext(
            framework="model", session_id=case.case_id,
            principal={"id": "validation-user", "role": "staff"},
            task={"goal": "Process the pending external notice"},
            sources=({"boundary": "external"},),
        )
        event = builder.build(
            "execute_enterprise_action", {"request_id": case.case_id}, context
        )
        assessment = engine.evaluate(event)
        results.append(assessment.level.value)
        print(f"{case.case_id}\t{assessment.level.value}\t{','.join(assessment.rule_ids)}")
    print("summary:", dict(sorted(Counter(results).items())))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
