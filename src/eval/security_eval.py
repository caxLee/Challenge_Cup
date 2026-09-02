from __future__ import annotations

import argparse

from .runner import SCENES, check_task, load_suite


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate the secured execution path")
    parser.add_argument("--scene", choices=(*SCENES, "all"), default="all")
    args = parser.parse_args()
    scenes = SCENES if args.scene == "all" else (args.scene,)

    normal_passed = normal_total = attacks_blocked = attacks_total = 0
    for scene in scenes:
        suite = load_suite(scene)
        normal = [check_task(scene, task, suite, secure=True) for task in suite.user_tasks.values()]
        attacks = [check_task(scene, task, suite, secure=True) for task in suite.injection_tasks.values()]
        scene_normal = sum(result.passed for result in normal)
        scene_blocked = sum(not result.passed for result in attacks)
        normal_passed += scene_normal
        normal_total += len(normal)
        attacks_blocked += scene_blocked
        attacks_total += len(attacks)
        print(f"{scene}: normal {scene_normal}/{len(normal)}, attacks blocked {scene_blocked}/{len(attacks)}")

    print(f"total: normal {normal_passed}/{normal_total}, attacks blocked {attacks_blocked}/{attacks_total}")
    return 0 if normal_passed == normal_total and attacks_blocked == attacks_total else 1


if __name__ == "__main__":
    raise SystemExit(main())
