from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import argparse
from pathlib import Path

from src.akira_engine.goldset import build_gold_review_bundle, render_gold_review_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a human-review goldset bundle from a scoring manifest.",
    )
    parser.add_argument(
        "--scoring-manifest",
        required=True,
        type=Path,
        help="Path to a Songwriter V2 scoring_manifest.json file.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("datasets") / "goldset_review",
        help="Directory where review packets and JSONL will be written.",
    )
    parser.add_argument(
        "--min-score",
        type=float,
        default=88.0,
        help="Minimum score required to include a lyric in the review bundle.",
    )
    parser.add_argument(
        "--max-records",
        type=int,
        help="Optional cap on the number of records to export.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    scoring_manifest = args.scoring_manifest.resolve()
    output_dir = args.output_dir if args.output_dir.is_absolute() else (Path.cwd() / args.output_dir).resolve()

    manifest = build_gold_review_bundle(
        scoring_manifest,
        output_dir,
        min_score=args.min_score,
        max_records=args.max_records,
    )

    report_path = output_dir / "gold_review_report.md"
    report_path.write_text(render_gold_review_report(manifest), encoding="utf-8")

    print(f"Manifest: {manifest['manifest_path']}")
    print(f"Report: {report_path}")
    print(f"Record count: {manifest['record_count']}")


if __name__ == "__main__":
    main()
