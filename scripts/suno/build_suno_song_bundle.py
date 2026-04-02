from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import argparse
from pathlib import Path

from src.akira_engine.suno_package import (
    build_suno_bundle_from_scoring_manifest,
    render_suno_bundle_report,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build SUNO-ready song packages that pair style prompt and full lyrics.",
    )
    parser.add_argument(
        "--scoring-manifest",
        required=True,
        type=Path,
        help="Path to a Songwriter V2 scoring_manifest.json file.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs") / "suno_song_bundle",
        help="Directory where SUNO song packages will be written.",
    )
    parser.add_argument(
        "--min-score",
        type=float,
        default=90.0,
        help="Minimum score required to export a song package.",
    )
    parser.add_argument(
        "--max-records",
        type=int,
        help="Optional cap on the number of packages to export.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    scoring_manifest = args.scoring_manifest.resolve()
    output_dir = args.output_dir if args.output_dir.is_absolute() else (Path.cwd() / args.output_dir).resolve()

    manifest = build_suno_bundle_from_scoring_manifest(
        scoring_manifest,
        output_dir,
        min_score=args.min_score,
        max_records=args.max_records,
    )
    report_path = output_dir / "suno_bundle_report.md"
    report_path.write_text(render_suno_bundle_report(manifest), encoding="utf-8")

    print(f"Manifest: {manifest['manifest_path']}")
    print(f"Report: {report_path}")
    print(f"Record count: {manifest['record_count']}")


if __name__ == "__main__":
    main()
