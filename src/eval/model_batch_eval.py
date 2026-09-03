"""Run a small protected batch through the real model tool loop."""

from __future__ import annotations

import argparse
import os
from collections import Counter

from dotenv import load_dotenv

from .cases import load_attack_cases
from .model_eval import _run


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()
    load_dotenv()
    if not os.getenv("MODEL_API_KEY"):
        raise RuntimeError("MODEL_API_KEY is not configured")
    outcomes: Counter[str] = Counter()
    levels: Counter[str] = Counter()
    for case in load_attack_cases()[:args.limit]:
        succeeded, _, tools, case_levels = _run(case, protected=True)
        outcome = "executed" if succeeded else "stopped"
        outcomes[outcome] += 1
        levels.update(case_levels)
        print(f"{case.case_id}\t{outcome}\ttools={tools}\tlevels={case_levels}")
    print("outcomes:", dict(outcomes))
    print("tool_call_levels:", dict(levels))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
