from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import argparse
from pathlib import Path

from src.akira_engine.reporting import render_artist_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render a human-readable style report from artist and track analysis JSON files."
    )
    parser.add_argument(
        "--artist-analysis",
        required=True,
        type=Path,
        help="Path to an artist analysis JSON file.",
    )
    parser.add_argument(
        "--track-analysis-dir",
        type=Path,
        default=Path("lyrics") / "analyzed" / "tracks",
        help="Root directory containing track analysis JSON files.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional markdown output path.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = render_artist_report(
        artist_analysis_path=args.artist_analysis,
        track_analysis_root=args.track_analysis_dir,
        output_path=args.output,
    )
    print(f"Generated style report: {summary.output_path}")


if __name__ == "__main__":
    main()
