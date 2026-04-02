from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import argparse
from pathlib import Path

from src.akira_engine.eval_benchmark import render_benchmark_report, score_prediction_dir


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Score artist eval prediction files against held-out eval sets.",
    )
    parser.add_argument(
        "--artist-id",
        required=True,
        help="artist_id to score, for example 'ado'.",
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
        "--predictions-dir",
        required=True,
        type=Path,
        help="Directory containing task-named prediction JSONL files.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Optional score output directory. Defaults to datasets/eval_scores/<artist_id>/<model_name>/.",
    )
    parser.add_argument(
        "--output-report",
        type=Path,
        help="Optional markdown report path. Defaults to reports/quality/<artist_id>_eval_scoring.md.",
    )
    parser.add_argument(
        "--model-name",
        help="Optional model label override.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    project_root = args.project_root.resolve()
    eval_dir = args.eval_dir or (Path("datasets") / "evals" / args.artist_id)
    final_eval_dir = eval_dir if eval_dir.is_absolute() else (project_root / eval_dir).resolve()

    predictions_dir = args.predictions_dir if args.predictions_dir.is_absolute() else (project_root / args.predictions_dir).resolve()
    inferred_model_name = args.model_name or predictions_dir.name

    output_dir = args.output_dir or (Path("datasets") / "eval_scores" / args.artist_id / inferred_model_name)
    final_output_dir = output_dir if output_dir.is_absolute() else (project_root / output_dir).resolve()

    manifest = score_prediction_dir(
        final_eval_dir,
        predictions_dir=predictions_dir,
        output_dir=final_output_dir,
        model_name=inferred_model_name,
    )

    report_path = args.output_report or (Path("reports") / "quality" / f"{args.artist_id}_eval_scoring.md")
    final_report_path = report_path if report_path.is_absolute() else (project_root / report_path).resolve()
    final_report_path.parent.mkdir(parents=True, exist_ok=True)
    final_report_path.write_text(render_benchmark_report(manifest), encoding="utf-8")

    print(f"Scoring manifest: {manifest['manifest_path']}")
    print(f"Scoring report: {final_report_path}")
    print(f"Overall average score: {manifest['overall_summary']['average_score']}")


if __name__ == "__main__":
    main()
