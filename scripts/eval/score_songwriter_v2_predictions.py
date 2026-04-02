from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import argparse
from pathlib import Path

from src.akira_engine.songwriter_v2_scoring import render_scoring_report, score_external_predictions


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Score external lyric predictions against Songwriter V2 run plans.",
    )
    parser.add_argument(
        "--run-root",
        required=True,
        type=Path,
        help="Root directory containing Songwriter V2 run folders.",
    )
    parser.add_argument(
        "--predictions-dir",
        required=True,
        type=Path,
        help="Directory containing external predictions named <track_id>.md.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("reports") / "quality" / "songwriter_v2_scoring",
        help="Directory where scoring artifacts will be written.",
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
    predictions_dir = (
        args.predictions_dir if args.predictions_dir.is_absolute() else (Path.cwd() / args.predictions_dir).resolve()
    )
    output_dir = args.output_dir if args.output_dir.is_absolute() else (Path.cwd() / args.output_dir).resolve()

    payload = score_external_predictions(run_root, predictions_dir, output_dir)

    report_path = args.report or (output_dir / "scoring_report.md")
    final_report_path = report_path if report_path.is_absolute() else (Path.cwd() / report_path).resolve()
    final_report_path.parent.mkdir(parents=True, exist_ok=True)
    final_report_path.write_text(render_scoring_report(payload), encoding="utf-8")

    print(f"Scoring manifest: {payload['manifest_path']}")
    print(f"Scoring report: {final_report_path}")
    print(f"Reviewed predictions: {payload['summary']['count']}")
    print(f"Average total: {payload['summary']['average_total']}")


if __name__ == "__main__":
    main()
