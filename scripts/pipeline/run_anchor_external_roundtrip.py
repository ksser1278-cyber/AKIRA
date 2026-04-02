from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run anchor external conditioning roundtrip.")
    parser.add_argument("--artist-id", required=True)
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--backup", action="store_true")
    return parser.parse_args()


def run_step(command: list[str], cwd: Path) -> None:
    completed = subprocess.run(command, cwd=str(cwd), check=False)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def main() -> None:
    args = parse_args()
    project_root = Path(args.project_root).resolve()
    input_dir = Path(args.input_dir).resolve()
    backup_flag = ["--backup"] if args.backup else []

    steps = [
        [
            sys.executable,
            str(project_root / "scripts" / "pipeline" / "validate_external_conditioning.py"),
            "--artist-id",
            args.artist_id,
            "--input-dir",
            str(input_dir),
            "--project-root",
            str(project_root),
        ],
        [
            sys.executable,
            str(project_root / "scripts" / "pipeline" / "merge_external_conditioning.py"),
            "--artist-id",
            args.artist_id,
            "--input-dir",
            str(input_dir),
            "--project-root",
            str(project_root),
            *backup_flag,
        ],
        [
            sys.executable,
            str(project_root / "scripts" / "pipeline" / "audit_conditioning_records.py"),
            "--artist-id",
            args.artist_id,
            "--project-root",
            str(project_root),
            "--active-queue-only",
        ],
        [
            sys.executable,
            str(project_root / "scripts" / "pipeline" / "report_engine_health.py"),
        ],
        [
            sys.executable,
            str(project_root / "scripts" / "pipeline" / "report_execution_backlog.py"),
        ],
        [
            sys.executable,
            str(project_root / "scripts" / "pipeline" / "report_external_handoff_index.py"),
        ],
    ]

    for step in steps:
        run_step(step, project_root)


if __name__ == "__main__":
    main()
