from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.akira_engine.demo_planner import build_demo_plan, render_demo_plan_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build an artist-synthesis demo plan from anchor, expansion, and mode-support evidence.",
    )
    parser.add_argument("--artist-id", required=True, help="Artist id such as deco27 or pinocchiop.")
    parser.add_argument("--mode-id", help="Optional target mode id. Defaults to representative profile priority.")
    parser.add_argument("--intent", help="Optional high-level demo intent.")
    parser.add_argument("--title-seed", help="Optional title seed for the composite plan.")
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Project root. Defaults to current working directory.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs") / "demo_planner",
        help="Output directory root.",
    )
    return parser.parse_args()


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    project_root = args.project_root.resolve()
    output_root = args.output_dir if args.output_dir.is_absolute() else (project_root / args.output_dir).resolve()

    plan = build_demo_plan(
        project_root,
        args.artist_id,
        mode_id=args.mode_id,
        intent=args.intent or "",
        title_seed=args.title_seed or "",
    )

    output_dir = output_root / args.artist_id / plan["mode_id"]
    output_dir.mkdir(parents=True, exist_ok=True)

    plan_path = output_dir / "demo_plan.json"
    report_path = output_dir / "demo_plan_report.md"
    _write_json(plan_path, plan)
    report_path.write_text(render_demo_plan_report(plan), encoding="utf-8")

    print(f"Demo plan: {plan_path}")
    print(f"Demo plan report: {report_path}")


if __name__ == "__main__":
    main()
