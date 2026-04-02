from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import argparse
from pathlib import Path

from src.akira_engine.songwriter_v2_batch import (
    render_songwriter_v2_batch_report,
    run_songwriter_v2_batch,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Songwriter V2 over a diverse subset of full_song_brief records.",
    )
    parser.add_argument(
        "--source-jsonl",
        required=True,
        type=Path,
        help="JSONL file containing full_song_brief records.",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=12,
        help="Number of tracks to run.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("outputs") / "songwriter_v2_batch",
        help="Root directory for batch outputs.",
    )
    parser.add_argument(
        "--existing-output-root",
        type=Path,
        help="Optional existing root used to exclude already-run track_ids.",
    )
    parser.add_argument(
        "--candidate-count",
        type=int,
        default=12,
        help="Number of candidates to generate per track.",
    )
    parser.add_argument(
        "--report",
        type=Path,
        help="Optional markdown report path.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    source_jsonl = args.source_jsonl.resolve()
    output_root = args.output_root if args.output_root.is_absolute() else (Path.cwd() / args.output_root).resolve()
    existing_root = None
    if args.existing_output_root:
        existing_root = (
            args.existing_output_root
            if args.existing_output_root.is_absolute()
            else (Path.cwd() / args.existing_output_root).resolve()
        )

    manifest = run_songwriter_v2_batch(
        source_jsonl,
        count=args.count,
        output_root=output_root,
        candidate_count=args.candidate_count,
        existing_output_root=existing_root,
    )

    report_path = args.report or (output_root / "batch_report.md")
    final_report_path = report_path if report_path.is_absolute() else (Path.cwd() / report_path).resolve()
    final_report_path.parent.mkdir(parents=True, exist_ok=True)
    final_report_path.write_text(render_songwriter_v2_batch_report(manifest), encoding="utf-8")

    print(f"Batch manifest: {manifest['manifest_path']}")
    print(f"Batch report: {final_report_path}")
    print(f"Average selected score: {manifest['summary']['average_selected_score']}")


if __name__ == "__main__":
    main()
