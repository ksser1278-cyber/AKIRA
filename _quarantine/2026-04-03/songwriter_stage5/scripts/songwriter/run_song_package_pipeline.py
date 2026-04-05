from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.akira_engine.gemini_songwriter import (  # noqa: E402
    DEFAULT_API_URL,
    DEFAULT_MODEL,
    run_gemini_request_bundle,
)
from src.akira_engine.songwriter_v2 import render_run_report, run_songwriter_v2  # noqa: E402
from src.akira_engine.songwriter_v2_exchange import (  # noqa: E402
    export_request_bundle,
    import_prediction_bundle,
)
from src.akira_engine.songwriter_v2_scoring import (  # noqa: E402
    render_scoring_report,
    score_external_predictions,
)
from src.akira_engine.suno_package import (  # noqa: E402
    build_suno_bundle_from_scoring_manifest,
    render_suno_bundle_report,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the end-to-end song package pipeline: planning, external generation, scoring, and SUNO bundle export.",
    )
    parser.add_argument(
        "--source-jsonl",
        required=True,
        type=Path,
        help="JSONL file containing full_song_brief records.",
    )
    parser.add_argument(
        "--track-id",
        help="Optional track_id to target a single track.",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Project root containing config/.env and outputs directories.",
    )
    parser.add_argument(
        "--candidate-count",
        type=int,
        default=12,
        help="Number of internal draft candidates to generate before exporting to an external model.",
    )
    parser.add_argument(
        "--external-mode",
        choices=["export-only", "gemini", "import-jsonl"],
        default="export-only",
        help="How to handle the external generation stage.",
    )
    parser.add_argument(
        "--predictions-jsonl",
        type=Path,
        help="External predictions JSONL to import when --external-mode=import-jsonl.",
    )
    parser.add_argument(
        "--work-dir",
        type=Path,
        help="Working directory for pipeline artifacts. Defaults to outputs/song_package_pipeline/<track_id or batch>.",
    )
    parser.add_argument(
        "--bundle-dir",
        type=Path,
        help="Directory for SUNO-ready bundles. Defaults to <work-dir>/suno_bundle.",
    )
    parser.add_argument(
        "--min-score",
        type=float,
        default=85.0,
        help="Minimum external score required to export a SUNO bundle.",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help="Gemini model name when --external-mode=gemini.",
    )
    parser.add_argument(
        "--api-url",
        default=DEFAULT_API_URL,
        help="Gemini API base URL when --external-mode=gemini.",
    )
    parser.add_argument("--timeout-seconds", type=int, default=120)
    parser.add_argument("--temperature", type=float, default=0.95)
    parser.add_argument("--top-p", type=float, default=0.95)
    parser.add_argument("--max-output-tokens", type=int, default=3072)
    parser.add_argument("--thinking-level")
    parser.add_argument("--retry-attempts", type=int, default=4)
    parser.add_argument("--sleep-seconds", type=float, default=1.5)
    parser.add_argument("--max-requests", type=int)
    return parser.parse_args()


def resolve_dir(base: Path, value: Path | None, fallback: Path) -> Path:
    if value is None:
        value = fallback
    return value if value.is_absolute() else (base / value).resolve()


def main() -> None:
    args = parse_args()
    project_root = args.project_root.resolve()
    source_jsonl = args.source_jsonl if args.source_jsonl.is_absolute() else (project_root / args.source_jsonl).resolve()

    stem = args.track_id or "batch"
    work_dir = resolve_dir(
        project_root,
        args.work_dir,
        Path("outputs") / "song_package_pipeline" / stem,
    )
    bundle_dir = resolve_dir(
        project_root,
        args.bundle_dir,
        work_dir / "suno_bundle",
    )

    run_dir = work_dir / "planner_run"
    manifest = run_songwriter_v2(
        source_jsonl,
        track_id=args.track_id,
        output_dir=run_dir,
        candidate_count=args.candidate_count,
    )
    run_report_path = run_dir / "run_report.md"
    run_report_path.write_text(render_run_report(manifest), encoding="utf-8")

    request_bundle = export_request_bundle(run_dir, work_dir / "request_bundle")

    print(f"Planner run manifest: {manifest['manifest_path']}")
    print(f"Planner run report: {run_report_path}")
    print(f"Request bundle: {request_bundle['manifest_path']}")

    if args.external_mode == "export-only":
        print("External generation was skipped. Use requests.jsonl with your generator, then rerun with --external-mode import-jsonl.")
        return

    if args.external_mode == "gemini":
        external_run = run_gemini_request_bundle(
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
            max_requests=args.max_requests,
        )
        predictions_jsonl = Path(external_run["predictions_jsonl"])
        print(f"Gemini run: {external_run['manifest_path']}")
    else:
        if args.predictions_jsonl is None:
            raise SystemExit("--predictions-jsonl is required when --external-mode=import-jsonl")
        predictions_jsonl = (
            args.predictions_jsonl
            if args.predictions_jsonl.is_absolute()
            else (project_root / args.predictions_jsonl).resolve()
        )
        if not predictions_jsonl.exists():
            raise SystemExit(f"Predictions JSONL not found: {predictions_jsonl}")

    imported = import_prediction_bundle(predictions_jsonl, work_dir / "imported_predictions")
    scoring = score_external_predictions(run_dir, work_dir / "imported_predictions", work_dir / "scoring")
    scoring_report_path = work_dir / "scoring" / "scoring_report.md"
    scoring_report_path.write_text(render_scoring_report(scoring), encoding="utf-8")

    suno_manifest = build_suno_bundle_from_scoring_manifest(
        Path(scoring["manifest_path"]),
        bundle_dir,
        min_score=args.min_score,
        max_records=None,
    )
    suno_report_path = bundle_dir / "suno_bundle_report.md"
    suno_report_path.write_text(render_suno_bundle_report(suno_manifest), encoding="utf-8")

    print(f"Imported predictions: {imported['manifest_path']}")
    print(f"Scoring manifest: {scoring['manifest_path']}")
    print(f"Scoring report: {scoring_report_path}")
    print(f"Average external score: {scoring['summary']['average_total']}")
    print(f"SUNO bundle manifest: {suno_manifest['manifest_path']}")
    print(f"SUNO bundle report: {suno_report_path}")
    print(f"SUNO bundle record count: {suno_manifest['record_count']}")


if __name__ == "__main__":
    main()
