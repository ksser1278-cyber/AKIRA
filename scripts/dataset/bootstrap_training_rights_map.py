from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import argparse

from src.akira_engine.cli import run_bootstrap_training_rights


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Bootstrap or refresh AKIRA training rights map entries from derived track-blueprint JSONL.",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Project root.",
    )
    parser.add_argument(
        "--derived-jsonl",
        type=Path,
        default=Path("datasets") / "training" / "track_blueprints.jsonl",
        help="Derived track blueprint JSONL.",
    )
    parser.add_argument(
        "--existing-map",
        type=Path,
        help="Optional existing rights map JSON to merge into the refreshed output.",
    )
    parser.add_argument(
        "--output-path",
        type=Path,
        default=Path("datasets") / "_global" / "training_rights_map.json",
        help="Output rights map path.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = run_bootstrap_training_rights(
        project_root=args.project_root.resolve(),
        derived_jsonl=args.derived_jsonl,
        existing_map=args.existing_map,
        output_path=args.output_path,
    )
    print(f"Rights map: {payload['output_path']}")
    print(f"Records: {len(payload['records'])}")


if __name__ == "__main__":
    main()
