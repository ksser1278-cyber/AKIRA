from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import argparse
from pathlib import Path

from src.akira_engine.analysis import analyze_tracks


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyze normalized lyric documents into track-level evidence JSON."
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("lyrics") / "normalized",
        help="Directory containing normalized lyric JSON files.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("lyrics") / "analyzed" / "tracks",
        help="Directory where track analysis JSON files will be written.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summaries = analyze_tracks(args.input_dir, args.output_dir)
    print(f"Track analyses generated: {len(summaries)}")
    for summary in summaries:
        print(
            f"- {summary.output_path} | hooks={summary.hook_count} | imagery={summary.dominant_imagery_tags}"
        )


if __name__ == "__main__":
    main()
