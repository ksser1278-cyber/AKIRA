from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import argparse
from pathlib import Path

from src.akira_engine.gemini_songwriter import (
    DEFAULT_API_URL,
    DEFAULT_MODEL,
    render_gemini_run_report,
    run_gemini_request_bundle,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a Songwriter V2 request bundle through the Gemini API.",
    )
    parser.add_argument(
        "--requests-jsonl",
        required=True,
        type=Path,
        help="JSONL file exported from Songwriter V2 request bundles.",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Project root containing config/.env if needed.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs") / "gemini_songwriter_run",
        help="Directory where Gemini outputs will be written.",
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
        default=0.9,
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
    parser.add_argument(
        "--report",
        type=Path,
        help="Optional markdown report path.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    requests_jsonl = args.requests_jsonl.resolve()
    project_root = args.project_root.resolve()
    output_dir = args.output_dir if args.output_dir.is_absolute() else (project_root / args.output_dir).resolve()

    manifest = run_gemini_request_bundle(
        requests_jsonl,
        project_root=project_root,
        output_dir=output_dir,
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

    report_path = args.report or (output_dir / "run_report.md")
    final_report_path = report_path if report_path.is_absolute() else (project_root / report_path).resolve()
    final_report_path.parent.mkdir(parents=True, exist_ok=True)
    final_report_path.write_text(render_gemini_run_report(manifest), encoding="utf-8")

    print(f"Run manifest: {manifest['manifest_path']}")
    print(f"Run report: {final_report_path}")
    print(f"Predictions JSONL: {manifest['predictions_jsonl']}")
    print(f"Success count: {manifest['summary']['success_count']}")


if __name__ == "__main__":
    main()
