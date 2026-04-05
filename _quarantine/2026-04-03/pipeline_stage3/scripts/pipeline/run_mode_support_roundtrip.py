from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run mode support external curation roundtrip.")
    parser.add_argument("--mode-id", required=True)
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--project-root", default=".")
    return parser.parse_args()


def run_step(command: list[str], cwd: Path) -> None:
    completed = subprocess.run(command, cwd=str(cwd), check=False)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def main() -> None:
    args = parse_args()
    project_root = Path(args.project_root).resolve()
    input_dir = Path(args.input_dir).resolve()
    steps = [
        [
            sys.executable,
            str(project_root / "scripts" / "pipeline" / "validate_mode_support_external.py"),
            "--mode-id",
            args.mode_id,
            "--input-dir",
            str(input_dir),
            "--project-root",
            str(project_root),
        ],
        [
            sys.executable,
            str(project_root / "scripts" / "pipeline" / "merge_mode_support_external.py"),
            "--mode-id",
            args.mode_id,
            "--input-dir",
            str(input_dir),
            "--project-root",
            str(project_root),
        ],
        [
            sys.executable,
            str(project_root / "scripts" / "pipeline" / "materialize_mode_support_scaffolds.py"),
            "--mode-id",
            args.mode_id,
            "--input-dir",
            str(input_dir),
            "--project-root",
            str(project_root),
        ],
        [
            sys.executable,
            str(project_root / "scripts" / "pipeline" / "report_mode_support_status.py"),
            "--project-root",
            str(project_root),
        ],
        [
            sys.executable,
            str(project_root / "scripts" / "pipeline" / "report_execution_backlog.py"),
        ],
        [
            sys.executable,
            str(project_root / "scripts" / "pipeline" / "report_engine_health.py"),
            "--artists",
            "pinocchiop",
            "deco27",
        ],
    ]
    for step in steps:
        run_step(step, project_root)


if __name__ == "__main__":
    main()
