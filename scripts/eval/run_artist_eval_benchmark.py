from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import argparse
from pathlib import Path

from src.akira_engine.eval_benchmark import render_benchmark_report, run_eval_benchmark


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a held-out single-artist eval benchmark with a deterministic baseline.",
    )
    parser.add_argument(
        "--artist-id",
        required=True,
        help="artist_id to benchmark, for example 'ado'.",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Project root containing datasets/ and reports/.",
    )
    parser.add_argument(
        "--eval-dir",
        type=Path,
        help="Optional eval set directory. Defaults to datasets/evals/<artist_id>/.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Optional benchmark output directory. Defaults to datasets/eval_runs/<artist_id>/heuristic_baseline_v1/.",
    )
    parser.add_argument(
        "--output-report",
        type=Path,
        help="Optional markdown report path. Defaults to reports/quality/<artist_id>_eval_benchmark.md.",
    )
    parser.add_argument(
        "--model-name",
        default="heuristic_baseline_v1",
        help="Label for the prediction source.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    project_root = args.project_root.resolve()
    eval_dir = args.eval_dir or (Path("datasets") / "evals" / args.artist_id)
    final_eval_dir = eval_dir if eval_dir.is_absolute() else (project_root / eval_dir).resolve()

    output_dir = args.output_dir or (Path("datasets") / "eval_runs" / args.artist_id / args.model_name)
    final_output_dir = output_dir if output_dir.is_absolute() else (project_root / output_dir).resolve()

    manifest = run_eval_benchmark(
        final_eval_dir,
        output_dir=final_output_dir,
        model_name=args.model_name,
    )

    report_path = args.output_report or (Path("reports") / "quality" / f"{args.artist_id}_eval_benchmark.md")
    final_report_path = report_path if report_path.is_absolute() else (project_root / report_path).resolve()
    final_report_path.parent.mkdir(parents=True, exist_ok=True)
    final_report_path.write_text(render_benchmark_report(manifest), encoding="utf-8")

    print(f"Benchmark manifest: {manifest['manifest_path']}")
    print(f"Benchmark report: {final_report_path}")
    print(f"Overall average score: {manifest['overall_summary']['average_score']}")
    for task_name, summary in manifest["task_summaries"].items():
        print(f"{task_name}: {summary['average_score']}")


if __name__ == "__main__":
    main()
