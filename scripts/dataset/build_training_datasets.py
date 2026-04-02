from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import argparse
from pathlib import Path

from src.akira_engine.audit import load_json
from src.akira_engine.training_data import build_training_datasets


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build training-ready derived datasets from audited lyric corpora.",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Project root that contains lyrics/, artists/, datasets/, and reports/.",
    )
    parser.add_argument(
        "--audit-json",
        type=Path,
        help="Optional corpus audit JSON. When provided, only artists and tracks that pass the threshold are used.",
    )
    parser.add_argument(
        "--minimum-recommendation",
        choices=["needs_review", "ready"],
        default="needs_review",
        help="Minimum audit recommendation required for artist inclusion.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("datasets") / "training",
        help="Output directory for derived training datasets.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    project_root = args.project_root.resolve()
    output_dir = args.output_dir if args.output_dir.is_absolute() else (project_root / args.output_dir).resolve()
    audit_payload = None
    if args.audit_json:
        audit_path = args.audit_json if args.audit_json.is_absolute() else (project_root / args.audit_json).resolve()
        audit_payload = load_json(audit_path)

    summary = build_training_datasets(
        project_root,
        audit_payload=audit_payload,
        minimum_recommendation=args.minimum_recommendation,
        output_dir=output_dir,
    )

    print(f"Training manifest: {summary['manifest_path']}")
    print(f"Track blueprints: {summary['counts']['track_blueprints']}")
    print(f"Artist style cards: {summary['counts']['artist_style_cards']}")


if __name__ == "__main__":
    main()
