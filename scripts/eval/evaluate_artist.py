from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import argparse
from pathlib import Path

from src.akira_engine.evaluation import evaluate_artist


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate how meaningful a single-artist lyric blueprint pipeline is."
    )
    parser.add_argument(
        "--artist",
        required=True,
        type=Path,
        help="Path to the artist profile JSON file.",
    )
    parser.add_argument(
        "--seeds",
        required=True,
        type=Path,
        help="Path to the seed JSON file.",
    )
    parser.add_argument(
        "--report",
        type=Path,
        help="Optional markdown report output path.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = evaluate_artist(
        profile_path=args.artist,
        seed_path=args.seeds,
        report_path=args.report,
    )
    print(f"Generated report: {summary.report_path}")
    print(f"Records reviewed: {summary.total_records}")
    print(f"Average score: {summary.average_score}")
    print(f"Strong records: {summary.strong_records}")


if __name__ == "__main__":
    main()
