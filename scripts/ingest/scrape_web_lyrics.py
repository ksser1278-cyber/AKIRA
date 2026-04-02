from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import argparse
import sys
from pathlib import Path

from src.akira_engine.web_scrape import scrape_web_manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scrape lyric pages from user-supplied URLs into raw text files and an ingest manifest."
    )
    parser.add_argument(
        "--web-manifest",
        required=True,
        type=Path,
        help="Path to a web scrape manifest JSON file.",
    )
    parser.add_argument(
        "--raw-dir",
        type=Path,
        help="Optional override for the raw lyric output directory.",
    )
    parser.add_argument(
        "--manifest-out",
        type=Path,
        help="Optional override for the generated ingest manifest path.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing raw lyric files if they already exist.",
    )
    return parser.parse_args()


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    args = parse_args()
    summary = scrape_web_manifest(
        args.web_manifest,
        raw_output_dir=args.raw_dir,
        manifest_output_path=args.manifest_out,
        overwrite=args.overwrite,
    )
    print(f"Raw lyric output: {summary.raw_output_dir}")
    print(f"Generated manifest: {summary.manifest_path}")
    print(f"Tracks scraped: {summary.track_count}")
    for track in summary.tracks:
        print(f"- {track.track_id}: {track.title} [{track.extraction_mode}]")


if __name__ == "__main__":
    main()
