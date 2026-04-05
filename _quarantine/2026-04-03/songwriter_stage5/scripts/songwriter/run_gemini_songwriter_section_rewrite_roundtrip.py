from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import argparse
from pathlib import Path

from src.akira_engine.gemini_songwriter import (
    DEFAULT_API_URL,
    DEFAULT_MODEL,
    run_gemini_request_bundle,
)
from src.akira_engine.songwriter_v2_revision import load_json
from src.akira_engine.songwriter_v2_scoring import render_scoring_report, score_external_predictions
from src.akira_engine.songwriter_v2_section_rewrite import (
    build_section_rewrite_request_bundle,
    merge_section_prediction_bundle,
    render_section_merge_report,
    render_section_rewrite_comparison_report,
    render_section_rewrite_request_report,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a section-level Gemini rewrite pass for low-scoring Songwriter V2 outputs.",
    )
    parser.add_argument(
        "--scoring-manifest",
        required=True,
        type=Path,
        help="Existing Songwriter V2 scoring_manifest.json used to select low-scoring tracks.",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Project root containing config/.env if needed.",
    )
    parser.add_argument(
        "--work-dir",
        type=Path,
        default=Path("outputs") / "gemini_songwriter_section_rewrite",
        help="Directory where request, prediction, and merged lyric artifacts will be written.",
    )
    parser.add_argument(
        "--score-dir",
        type=Path,
        default=Path("reports") / "quality" / "gemini_songwriter_section_rewrite",
        help="Directory where scoring artifacts will be written.",
    )
    parser.add_argument(
        "--score-threshold",
        type=float,
        default=88.0,
        help="Rewrite tracks whose total score is below this threshold.",
    )
    parser.add_argument(
        "--max-tracks",
        type=int,
        help="Optional cap on the number of tracks to revise.",
    )
    parser.add_argument(
        "--sections-per-track",
        type=int,
        default=1,
        help="How many weak sections to rewrite per selected track.",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help="Gemini model name.",
    )
    parser.add_argument(
        "--api-url",
        default=DEFAULT_API_URL,
        help="Gemini API base URL.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=120,
        help="Per-request timeout in seconds.",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.95,
        help="Sampling temperature.",
    )
    parser.add_argument(
        "--top-p",
        type=float,
        default=0.95,
        help="Top-p sampling parameter.",
    )
    parser.add_argument(
        "--max-output-tokens",
        type=int,
        default=3072,
        help="Maximum output tokens per request.",
    )
    parser.add_argument(
        "--thinking-level",
        help="Optional Gemini thinking level.",
    )
    parser.add_argument(
        "--retry-attempts",
        type=int,
        default=4,
        help="How many times to retry failed requests.",
    )
    parser.add_argument(
        "--sleep-seconds",
        type=float,
        default=1.5,
        help="Delay between requests.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    project_root = args.project_root.resolve()
    scoring_manifest = args.scoring_manifest.resolve()
    work_dir = args.work_dir if args.work_dir.is_absolute() else (project_root / args.work_dir).resolve()
    score_dir = args.score_dir if args.score_dir.is_absolute() else (project_root / args.score_dir).resolve()

    request_bundle = build_section_rewrite_request_bundle(
        scoring_manifest,
        work_dir / "request_bundle",
        score_threshold=args.score_threshold,
        max_tracks=args.max_tracks,
        sections_per_track=args.sections_per_track,
    )
    request_report_path = work_dir / "request_bundle" / "request_report.md"
    request_report_path.write_text(render_section_rewrite_request_report(request_bundle), encoding="utf-8")

    if request_bundle["request_count"] == 0:
        print("No section rewrite requests were generated.")
        return

    gemini_run = run_gemini_request_bundle(
        Path(request_bundle["requests_jsonl"]),
        project_root=project_root,
        output_dir=work_dir / "gemini_run",
        model=args.model,
        api_url=args.api_url,
        timeout_seconds=args.timeout_seconds,
        temperature=args.temperature,
        top_p=args.top_p,
        max_output_tokens=args.max_output_tokens,
        thinking_level=args.thinking_level,
        retry_attempts=args.retry_attempts,
        sleep_seconds=args.sleep_seconds,
    )

    merge_manifest = merge_section_prediction_bundle(
        Path(gemini_run["predictions_jsonl"]),
        work_dir / "merged_predictions",
    )
    merge_report_path = work_dir / "merged_predictions" / "merge_report.md"
    merge_report_path.write_text(render_section_merge_report(merge_manifest), encoding="utf-8")

    original_scoring = load_json(scoring_manifest)
    original_scoring["manifest_path"] = str(scoring_manifest)
    run_root = Path(original_scoring["run_root"])
    revised_scoring = score_external_predictions(run_root, work_dir / "merged_predictions", score_dir)

    scoring_report_path = score_dir / "section_rewrite_report.md"
    scoring_report_path.write_text(render_scoring_report(revised_scoring), encoding="utf-8")

    comparison_report_path = score_dir / "section_rewrite_comparison.md"
    comparison_report_path.write_text(
        render_section_rewrite_comparison_report(original_scoring, revised_scoring),
        encoding="utf-8",
    )

    print(f"Request bundle: {request_bundle['manifest_path']}")
    print(f"Gemini run: {gemini_run['manifest_path']}")
    print(f"Merge manifest: {merge_manifest['manifest_path']}")
    print(f"Revised scoring manifest: {revised_scoring['manifest_path']}")
    print(f"Comparison report: {comparison_report_path}")


if __name__ == "__main__":
    main()
