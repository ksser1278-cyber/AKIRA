from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import argparse
from pathlib import Path

from src.akira_engine.songwriter_v2 import render_run_report, run_songwriter_v2


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the Songwriter V2 planning, candidate generation, and critique pipeline.",
    )
    parser.add_argument(
        "--source-jsonl",
        required=True,
        type=Path,
        help="JSONL file containing full_song_brief records.",
    )
    parser.add_argument(
        "--track-id",
        help="Optional track_id to select a specific record. Defaults to the first record.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Optional run output directory. Defaults to outputs/songwriter_v2/<artist_id>/<track_id>/.",
    )
    parser.add_argument(
        "--candidate-count",
        type=int,
        default=12,
        help="Number of lyric candidates to generate before critique and reranking.",
    )
    parser.add_argument(
        "--report",
        type=Path,
        help="Optional markdown report output path.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    source_jsonl = args.source_jsonl.resolve()

    if args.output_dir is None:
        stem_track = args.track_id or "first_track"
        output_dir = Path("outputs") / "songwriter_v2" / "ado" / stem_track
    else:
        output_dir = args.output_dir
    final_output_dir = output_dir if output_dir.is_absolute() else (Path.cwd() / output_dir).resolve()

    manifest = run_songwriter_v2(
        source_jsonl,
        track_id=args.track_id,
        output_dir=final_output_dir,
        candidate_count=args.candidate_count,
    )

    report_path = args.report or (final_output_dir / "run_report.md")
    final_report_path = report_path if report_path.is_absolute() else (Path.cwd() / report_path).resolve()
    final_report_path.parent.mkdir(parents=True, exist_ok=True)
    final_report_path.write_text(render_run_report(manifest), encoding="utf-8")

    print(f"Run manifest: {manifest['manifest_path']}")
    print(f"Selected lyric: {manifest['selected_lyric_path']}")
    print(f"Run report: {final_report_path}")
    print(f"Winning candidate: {manifest['selected_candidate_id']}")
    print(f"Winning score: {manifest['selected_score']}")


if __name__ == "__main__":
    main()
