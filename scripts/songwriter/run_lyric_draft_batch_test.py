from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import argparse
from pathlib import Path

from src.akira_engine.lyric_draft_batch import render_batch_report, run_batch_draft_test


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate and review a batch of original lyric drafts from abstracted brief records.",
    )
    parser.add_argument(
        "--source-jsonl",
        required=True,
        type=Path,
        help="JSONL file containing full_song_brief or full_song_brief_eval records.",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=28,
        help="Number of additional drafts to generate.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Optional output directory. Defaults to outputs/lyric_drafts/<artist_id>/batch_design_test/.",
    )
    parser.add_argument(
        "--existing-output-root",
        type=Path,
        help="Optional root directory used to exclude already generated track_ids.",
    )
    parser.add_argument(
        "--report",
        type=Path,
        help="Optional markdown report output path.",
    )
    parser.add_argument(
        "--candidate-count",
        type=int,
        default=6,
        help="Number of draft variants to sample per record before reranking.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    source_jsonl = args.source_jsonl.resolve()
    records_root = source_jsonl.parent.parent.parent if "datasets" in str(source_jsonl) else Path.cwd()

    output_dir = args.output_dir
    if output_dir is None:
        output_dir = Path("outputs") / "lyric_drafts" / "ado" / "batch_design_test"
    final_output_dir = output_dir if output_dir.is_absolute() else (Path.cwd() / output_dir).resolve()

    existing_output_root = args.existing_output_root
    if existing_output_root is None:
        existing_output_root = Path("outputs") / "lyric_drafts" / "ado"
    final_existing_root = (
        existing_output_root if existing_output_root.is_absolute() else (Path.cwd() / existing_output_root).resolve()
    )

    manifest = run_batch_draft_test(
        source_jsonl,
        count=args.count,
        output_dir=final_output_dir,
        existing_output_root=final_existing_root,
        candidate_count=args.candidate_count,
    )

    report_path = args.report or (Path("reports") / "quality" / "ado_lyric_draft_batch_test.md")
    final_report_path = report_path if report_path.is_absolute() else (Path.cwd() / report_path).resolve()
    final_report_path.parent.mkdir(parents=True, exist_ok=True)
    final_report_path.write_text(render_batch_report(manifest), encoding="utf-8")

    print(f"Batch manifest: {manifest['manifest_path']}")
    print(f"Batch report: {final_report_path}")
    print(f"Drafts generated: {manifest['summary']['count']}")
    print(f"Average alignment score: {manifest['summary']['average_score']}")


if __name__ == "__main__":
    main()
