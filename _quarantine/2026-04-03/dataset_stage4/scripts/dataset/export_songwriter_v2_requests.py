from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import argparse
from pathlib import Path

from src.akira_engine.songwriter_v2_exchange import (
    export_request_bundle,
    render_request_bundle_report,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export Songwriter V2 prompt packages into a model-ready request bundle.",
    )
    parser.add_argument(
        "--run-root",
        required=True,
        type=Path,
        help="Root directory containing Songwriter V2 run folders.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs") / "songwriter_v2_requests",
        help="Directory where request artifacts will be written.",
    )
    parser.add_argument(
        "--report",
        type=Path,
        help="Optional markdown report path.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_root = args.run_root if args.run_root.is_absolute() else (Path.cwd() / args.run_root).resolve()
    output_dir = args.output_dir if args.output_dir.is_absolute() else (Path.cwd() / args.output_dir).resolve()

    manifest = export_request_bundle(run_root, output_dir)

    report_path = args.report or (output_dir / "request_report.md")
    final_report_path = report_path if report_path.is_absolute() else (Path.cwd() / report_path).resolve()
    final_report_path.parent.mkdir(parents=True, exist_ok=True)
    final_report_path.write_text(render_request_bundle_report(manifest), encoding="utf-8")

    print(f"Request manifest: {manifest['manifest_path']}")
    print(f"Request report: {final_report_path}")
    print(f"Request count: {manifest['request_count']}")


if __name__ == "__main__":
    main()
