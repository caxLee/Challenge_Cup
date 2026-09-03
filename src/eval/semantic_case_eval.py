"""Evaluate runtime-visible attack text with the isolated semantic analyzer."""

from __future__ import annotations

import argparse
import os

from dotenv import load_dotenv
from openai import OpenAI

from adapters import ModelRiskAnalyzer
from core import EventBuilder, ExecutionContext, RuleRiskEngine
from .cases import load_attack_cases
from .model_eval import TOOL_MANIFEST


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=5)
    args = parser.parse_args()
    load_dotenv()
    client = OpenAI(
        api_key=os.environ["MODEL_API_KEY"],
        base_url=os.getenv("MODEL_BASE_URL", "https://ai.stackway.org/v1"),
        timeout=60.0,
        max_retries=1,
    )
    analyzer = ModelRiskAnalyzer(client, os.getenv("MODEL_NAME", "deepseek-v4-flash"))
    builder = EventBuilder(TOOL_MANIFEST)
    engine = RuleRiskEngine()
    for case in load_attack_cases()[:args.limit]:
        analysis = analyzer.analyze(
            task={"goal": "Process the pending enterprise request"},
            observations=[case.attacker_instruction],
            tool_name="execute_enterprise_action",
            arguments={"request_id": case.case_id},
        )
        context = ExecutionContext(
            framework="semantic-eval",
            session_id=case.case_id,
            principal={"id": "eval-user", "role": "staff"},
            sources=({"boundary": "external"},),
            risk_signals=analysis.signals if analysis.confidence >= 0.7 else (),
        )
        assessment = engine.evaluate(builder.build(
            "execute_enterprise_action", {"request_id": case.case_id}, context
        ))
        print(
            f"{case.case_id}\t{assessment.level.value}\t"
            f"confidence={analysis.confidence:.2f}\tsignals={list(analysis.signals)}\t"
            f"evidence={list(analysis.evidence)}\terror={analysis.error}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
