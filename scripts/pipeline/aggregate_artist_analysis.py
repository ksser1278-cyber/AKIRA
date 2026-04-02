from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import argparse
from pathlib import Path

from src.akira_engine.analysis import aggregate_artist_analyses


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Aggregate track-level lyric analyses into artist-level style analyses."
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("lyrics") / "analyzed" / "tracks",
        help="Directory containing track analysis JSON files.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("lyrics") / "analyzed" / "artists",
        help="Directory where artist analysis JSON files will be written.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summaries = aggregate_artist_analyses(args.input_dir, args.output_dir)
    print(f"Artist analyses generated: {len(summaries)}")
    for summary in summaries:
        print(
            f"- {summary.output_path} | tracks={summary.track_count} | modes={summary.dominant_modes}"
        )


if __name__ == "__main__":
    main()
