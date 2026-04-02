from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import argparse
from pathlib import Path

from src.akira_engine.eval_sets import build_eval_sets, render_eval_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build held-out evaluation sets for a single artist package.",
    )
    parser.add_argument(
        "--artist-id",
        required=True,
        help="artist_id to build eval sets for, for example 'ado'.",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Project root containing datasets/ and reports/.",
    )
    parser.add_argument(
        "--package-dir",
        type=Path,
        help="Optional artist package directory. Defaults to datasets/training/<artist_id>/.",
    )
    parser.add_argument(
        "--experiments-dir",
        type=Path,
        help="Optional experiment directory. Defaults to datasets/experiments/<artist_id>/.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Optional eval output directory. Defaults to datasets/evals/<artist_id>/.",
    )
    parser.add_argument(
        "--output-report",
        type=Path,
        help="Optional markdown report path. Defaults to reports/quality/<artist_id>_eval_sets.md.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    project_root = args.project_root.resolve()
    package_dir = args.package_dir or (Path("datasets") / "training" / args.artist_id)
    final_package_dir = package_dir if package_dir.is_absolute() else (project_root / package_dir).resolve()

    experiments_dir = args.experiments_dir or (Path("datasets") / "experiments" / args.artist_id)
    final_experiments_dir = (
        experiments_dir if experiments_dir.is_absolute() else (project_root / experiments_dir).resolve()
    )

    output_dir = args.output_dir or (Path("datasets") / "evals" / args.artist_id)
    final_output_dir = output_dir if output_dir.is_absolute() else (project_root / output_dir).resolve()

    manifest = build_eval_sets(
        final_package_dir,
        experiments_dir=final_experiments_dir,
        output_dir=final_output_dir,
    )

    report_path = args.output_report or (Path("reports") / "quality" / f"{args.artist_id}_eval_sets.md")
    final_report_path = report_path if report_path.is_absolute() else (project_root / report_path).resolve()
    final_report_path.parent.mkdir(parents=True, exist_ok=True)
    final_report_path.write_text(render_eval_report(manifest), encoding="utf-8")

    print(f"Eval manifest: {manifest['manifest_path']}")
    print(f"Eval report: {final_report_path}")
    for task_name, count in manifest["counts"].items():
        print(f"{task_name}: {count}")


if __name__ == "__main__":
    main()
