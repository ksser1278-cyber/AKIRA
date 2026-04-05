from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run generation_safety grounding external roundtrip.")
    parser.add_argument("--artist-id", required=True)
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--backup", action="store_true")
    return parser.parse_args()


def run_step(command: list[str], cwd: Path) -> None:
    completed = subprocess.run(command, cwd=str(cwd), check=False)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def validation_manifest_path(project_root: Path, artist_id: str) -> Path:
    return (
        project_root
        / "reports"
        / "quality"
        / "external_validation"
        / f"{artist_id}_generation_safety_grounding_external_validation.json"
    )


def assert_clean_validation(project_root: Path, artist_id: str) -> None:
    manifest_path = validation_manifest_path(project_root, artist_id)
    if not manifest_path.exists():
        raise SystemExit(f"Grounding validation manifest not found: {manifest_path}")
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    invalid_count = int(payload.get("invalid_count", 0))
    if invalid_count > 0:
        raise SystemExit(
            f"Grounding validation failed for {artist_id}: invalid_count={invalid_count}. "
            "Merge aborted."
        )


def main() -> None:
    args = parse_args()
    project_root = Path(args.project_root).resolve()
    input_dir = Path(args.input_dir).resolve()
    backup_flag = ["--backup"] if args.backup else []

    validate_step = [
        sys.executable,
        str(project_root / "scripts" / "pipeline" / "validate_generation_safety_grounding_external.py"),
        "--artist-id",
        args.artist_id,
        "--input-dir",
        str(input_dir),
        "--project-root",
        str(project_root),
    ]
    run_step(validate_step, project_root)
    assert_clean_validation(project_root, args.artist_id)

    steps = [
        [
            sys.executable,
            str(project_root / "scripts" / "pipeline" / "merge_generation_safety_grounding_external.py"),
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
            str(project_root / "scripts" / "pipeline" / "apply_generation_safety_pilot.py"),
            "--overwrite",
        ],
        [
            sys.executable,
            str(project_root / "scripts" / "pipeline" / "report_generation_safety_promotion_queue.py"),
        ],
        [
            sys.executable,
            str(project_root / "scripts" / "pipeline" / "build_generation_safety_promotion_handoff.py"),
        ],
        [
            sys.executable,
            str(project_root / "scripts" / "pipeline" / "build_generation_safety_grounding_handoff.py"),
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
