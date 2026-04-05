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
from src.akira_engine.songwriter_v2_exchange import export_request_bundle, import_prediction_bundle
from src.akira_engine.songwriter_v2_scoring import render_scoring_report, score_external_predictions


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the full Songwriter V2 -> Gemini -> import -> score roundtrip.",
    )
    parser.add_argument(
        "--run-root",
        required=True,
        type=Path,
        help="Root directory containing Songwriter V2 run folders.",
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
        default=Path("outputs") / "gemini_songwriter_roundtrip",
        help="Directory where request, prediction, and import artifacts will be written.",
    )
    parser.add_argument(
        "--score-dir",
        type=Path,
        default=Path("reports") / "quality" / "gemini_songwriter_roundtrip",
        help="Directory where scoring artifacts will be written.",
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
    parser.add_argument(
        "--max-requests",
        type=int,
        help="Optional cap on the number of requests to send.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    project_root = args.project_root.resolve()
    run_root = args.run_root if args.run_root.is_absolute() else (project_root / args.run_root).resolve()
    work_dir = args.work_dir if args.work_dir.is_absolute() else (project_root / args.work_dir).resolve()
    score_dir = args.score_dir if args.score_dir.is_absolute() else (project_root / args.score_dir).resolve()

    request_bundle = export_request_bundle(run_root, work_dir / "request_bundle")
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
        max_requests=args.max_requests,
    )
    imported = import_prediction_bundle(Path(gemini_run["predictions_jsonl"]), work_dir / "imported_predictions")
    scoring = score_external_predictions(run_root, work_dir / "imported_predictions", score_dir)
    report_path = score_dir / "roundtrip_report.md"
    report_path.write_text(render_scoring_report(scoring), encoding="utf-8")

    print(f"Request bundle: {request_bundle['manifest_path']}")
    print(f"Gemini run: {gemini_run['manifest_path']}")
    print(f"Imported predictions: {imported['manifest_path']}")
    print(f"Scoring manifest: {scoring['manifest_path']}")
    print(f"Scoring report: {report_path}")
    print(f"Average total: {scoring['summary']['average_total']}")


if __name__ == "__main__":
    main()
