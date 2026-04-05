from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import argparse
from pathlib import Path

from src.akira_engine.corpus import build_all_datasets


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build lyric blueprint datasets for every artist that has profile.json and seeds.json."
    )
    parser.add_argument(
        "--artists-root",
        type=Path,
        default=Path("artists"),
        help="Root directory that contains artist subdirectories.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("datasets") / "processed",
        help="Directory where per-artist JSONL files will be written.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summaries = build_all_datasets(
        artists_root=args.artists_root,
        output_dir=args.output_dir,
    )

    print(f"Built datasets: {len(summaries)}")
    for summary in summaries:
        print(
            f"- {summary.output_path} | records={summary.total_records} | splits={summary.split_counts}"
        )


if __name__ == "__main__":
    main()
