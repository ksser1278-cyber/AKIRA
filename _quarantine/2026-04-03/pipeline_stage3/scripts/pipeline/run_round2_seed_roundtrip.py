from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run round2 seed intake roundtrip.")
    parser.add_argument("--artist-id", required=True)
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
            str(project_root / "scripts" / "pipeline" / "validate_round2_seed_external.py"),
            "--artist-id",
            args.artist_id,
            "--input-dir",
            str(input_dir),
            "--project-root",
            str(project_root),
        ],
        [
            sys.executable,
            str(project_root / "scripts" / "pipeline" / "merge_round2_seed_external.py"),
            "--artist-id",
            args.artist_id,
            "--input-dir",
            str(input_dir),
            "--project-root",
            str(project_root),
        ],
        [
            sys.executable,
            str(project_root / "scripts" / "pipeline" / "materialize_round2_seed_scaffolds.py"),
            "--project-root",
            str(project_root),
        ],
        [
            sys.executable,
            str(project_root / "scripts" / "pipeline" / "audit_round2_expansion.py"),
            "--artist-id",
            args.artist_id,
            "--project-root",
            str(project_root),
        ],
        [
            sys.executable,
            str(project_root / "scripts" / "pipeline" / "sync_round2_queue_status.py"),
            "--project-root",
            str(project_root),
        ],
        [
            sys.executable,
            str(project_root / "scripts" / "pipeline" / "report_round2_expansion_status.py"),
            "--project-root",
            str(project_root),
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
