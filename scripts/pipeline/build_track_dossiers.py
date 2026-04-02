from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.akira_engine.dossier import build_track_dossiers


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build richer track dossiers that borrow the manual deep-analysis format.",
    )
    parser.add_argument("--artist-id", required=True, help="Artist id to convert into dossier records.")
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path("."),
        help="Project root path.",
    )
    parser.add_argument(
        "--intent-root",
        type=Path,
        default=Path("datasets") / "intent",
        help="Root directory for track intent records.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("datasets") / "dossiers",
        help="Root directory where dossier JSONL outputs will be written.",
    )
    parser.add_argument(
        "--report-root",
        type=Path,
        default=Path("reports") / "dossiers",
        help="Directory where dossier reports will be written.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    project_root = args.project_root.resolve()
    intent_root = args.intent_root if args.intent_root.is_absolute() else (project_root / args.intent_root).resolve()
    output_root = args.output_root if args.output_root.is_absolute() else (project_root / args.output_root).resolve()
    report_root = args.report_root if args.report_root.is_absolute() else (project_root / args.report_root).resolve()

    manifest = build_track_dossiers(
        project_root=project_root,
        artist_id=args.artist_id,
        intent_root=intent_root,
        output_root=output_root,
        report_root=report_root,
    )
    print(f"Records: {manifest['records_path']}")
    print(f"Manifest: {manifest['manifest_path']}")
    print(f"Report: {manifest['report_path']}")
    print(f"Intent labels: {manifest['intent_label_counts']}")


if __name__ == "__main__":
    main()
