from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import argparse
from pathlib import Path

from src.akira_engine.songwriter_v2_bestof import (
    build_bestof_scoring_manifest,
    render_bestof_report,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Merge multiple Songwriter V2 scoring manifests and keep the best prediction per track.",
    )
    parser.add_argument(
        "--scoring-manifest",
        action="append",
        dest="scoring_manifests",
        required=True,
        type=Path,
        help="Scoring manifest to include. Pass this flag multiple times.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs") / "songwriter_v2_bestof",
        help="Directory for the merged best-of manifest and copied predictions.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifests = [path.resolve() for path in args.scoring_manifests]
    output_dir = args.output_dir if args.output_dir.is_absolute() else (Path.cwd() / args.output_dir).resolve()

    payload = build_bestof_scoring_manifest(manifests, output_dir)
    report_path = output_dir / "bestof_report.md"
    report_path.write_text(render_bestof_report(payload), encoding="utf-8")

    print(f"Manifest: {payload['manifest_path']}")
    print(f"Report: {report_path}")
    print(f"Average total: {payload['summary']['average_total']}")


if __name__ == "__main__":
    main()
