from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import argparse
from pathlib import Path

from src.akira_engine.dataset import build_dataset


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a JSONL lyric blueprint dataset from an artist profile and a seed file."
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
        help="Path to the dataset seed JSON file.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional JSONL output path. Defaults to datasets/processed/<artist>_lyric_blueprints.jsonl",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = build_dataset(
        profile_path=args.artist,
        seed_path=args.seeds,
        output_path=args.output,
    )
    print(f"Generated dataset: {summary.output_path}")
    print(f"Total records: {summary.total_records}")
    print(f"Split counts: {summary.split_counts}")


if __name__ == "__main__":
    main()
