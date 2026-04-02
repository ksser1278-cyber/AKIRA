from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.akira_engine.intent import build_track_intent_cards


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build track intent cards so song-purpose metadata can condition downstream generation.",
    )
    parser.add_argument("--artist-id", required=True, help="Artist id to enrich.")
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path("."),
        help="Project root path.",
    )
    parser.add_argument(
        "--curated-root",
        type=Path,
        default=Path("datasets") / "curated",
        help="Root directory for curated lyric records.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("datasets") / "intent",
        help="Root directory where track intent cards will be written.",
    )
    parser.add_argument(
        "--report-root",
        type=Path,
        default=Path("reports") / "intent",
        help="Directory where human-readable intent reports will be written.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    project_root = args.project_root.resolve()
    curated_root = args.curated_root if args.curated_root.is_absolute() else (project_root / args.curated_root).resolve()
    output_root = args.output_root if args.output_root.is_absolute() else (project_root / args.output_root).resolve()
    report_root = args.report_root if args.report_root.is_absolute() else (project_root / args.report_root).resolve()

    manifest = build_track_intent_cards(
        project_root=project_root,
        artist_id=args.artist_id,
        curated_root=curated_root,
        output_root=output_root,
        report_root=report_root,
    )
    print(f"Records: {manifest['records_path']}")
    print(f"Manifest: {manifest['intent_manifest_path']}")
    print(f"Report: {manifest['report_path']}")
    print(f"Intent labels: {manifest['intent_label_counts']}")


if __name__ == "__main__":
    main()
