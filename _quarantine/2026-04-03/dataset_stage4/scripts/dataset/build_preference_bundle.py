from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import argparse
from pathlib import Path

from src.akira_engine.goldset import build_preference_bundle, render_preference_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a pairwise preference bundle from two scoring manifests.",
    )
    parser.add_argument(
        "--left-scoring-manifest",
        required=True,
        type=Path,
        help="First scoring_manifest.json.",
    )
    parser.add_argument(
        "--right-scoring-manifest",
        required=True,
        type=Path,
        help="Second scoring_manifest.json.",
    )
    parser.add_argument(
        "--left-label",
        default="left_system",
        help="Human-readable label for the first manifest.",
    )
    parser.add_argument(
        "--right-label",
        default="right_system",
        help="Human-readable label for the second manifest.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("datasets") / "preference_review",
        help="Directory where preference packets and JSONL will be written.",
    )
    parser.add_argument(
        "--max-pairs",
        type=int,
        help="Optional cap on the number of pairs to export.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    left_scoring_manifest = args.left_scoring_manifest.resolve()
    right_scoring_manifest = args.right_scoring_manifest.resolve()
    output_dir = args.output_dir if args.output_dir.is_absolute() else (Path.cwd() / args.output_dir).resolve()

    manifest = build_preference_bundle(
        left_scoring_manifest,
        right_scoring_manifest,
        output_dir,
        left_label=args.left_label,
        right_label=args.right_label,
        max_pairs=args.max_pairs,
    )

    report_path = output_dir / "preference_report.md"
    report_path.write_text(render_preference_report(manifest), encoding="utf-8")

    print(f"Manifest: {manifest['manifest_path']}")
    print(f"Report: {report_path}")
    print(f"Pair count: {manifest['pair_count']}")


if __name__ == "__main__":
    main()
