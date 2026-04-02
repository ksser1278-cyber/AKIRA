from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import argparse
from pathlib import Path

from src.akira_engine.ingest import normalize_manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Normalize local lyric files into structured JSON documents."
    )
    parser.add_argument(
        "--manifest",
        required=True,
        type=Path,
        help="Path to a lyric source manifest JSON file.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Optional output root. Defaults to lyrics/normalized",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = normalize_manifest(args.manifest, args.output_dir)
    print(f"Normalized output: {summary.output_dir}")
    print(f"Tracks processed: {summary.total_tracks}")
    print(f"Sections detected: {summary.total_sections}")


if __name__ == "__main__":
    main()
