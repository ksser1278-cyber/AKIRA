from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.akira_engine.curation import curate_artist


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Promote normalized lyrics into a curated corpus that is safer to use for training.",
    )
    parser.add_argument(
        "--artist-id",
        required=True,
        help="Artist id whose normalized lyric directory should be curated.",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path("."),
        help="Project root path.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("datasets") / "curated",
        help="Directory where curated JSONL outputs will be written.",
    )
    parser.add_argument(
        "--report-root",
        type=Path,
        default=Path("reports") / "quality",
        help="Directory where curation reports will be written.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    project_root = args.project_root.resolve()
    output_root = args.output_root if args.output_root.is_absolute() else (project_root / args.output_root).resolve()
    report_root = args.report_root if args.report_root.is_absolute() else (project_root / args.report_root).resolve()

    manifest = curate_artist(
        project_root=project_root,
        artist_id=args.artist_id,
        output_root=output_root,
        report_root=report_root,
    )
    print(f"Records: {manifest['records_path']}")
    print(f"Manifest: {manifest['curation_manifest_path']}")
    print(f"Report: {manifest['report_path']}")
    print(f"Recommendation counts: {manifest['recommendation_counts']}")


if __name__ == "__main__":
    main()
