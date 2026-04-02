from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import argparse
from pathlib import Path

from src.akira_engine.experiment_sets import build_experiment_sets, render_experiment_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build artist-specific experiment instruction sets from a training package.",
    )
    parser.add_argument(
        "--artist-id",
        required=True,
        help="artist_id to build experiment sets for, for example 'ado'.",
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
        "--output-dir",
        type=Path,
        help="Optional experiment output directory. Defaults to datasets/experiments/<artist_id>/.",
    )
    parser.add_argument(
        "--output-report",
        type=Path,
        help="Optional markdown report path. Defaults to reports/quality/<artist_id>_experiment_sets.md.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    project_root = args.project_root.resolve()
    package_dir = args.package_dir or (Path("datasets") / "training" / args.artist_id)
    final_package_dir = package_dir if package_dir.is_absolute() else (project_root / package_dir).resolve()
    final_output_dir = args.output_dir or (Path("datasets") / "experiments" / args.artist_id)
    final_output_dir = final_output_dir if final_output_dir.is_absolute() else (project_root / final_output_dir).resolve()

    manifest = build_experiment_sets(final_package_dir, output_dir=final_output_dir)

    report_path = args.output_report or (Path("reports") / "quality" / f"{args.artist_id}_experiment_sets.md")
    final_report_path = report_path if report_path.is_absolute() else (project_root / report_path).resolve()
    final_report_path.parent.mkdir(parents=True, exist_ok=True)
    final_report_path.write_text(render_experiment_report(manifest), encoding="utf-8")

    print(f"Experiment manifest: {manifest['manifest_path']}")
    print(f"Experiment report: {final_report_path}")
    for task_name, count in manifest["counts"].items():
        print(f"{task_name}: {count}")


if __name__ == "__main__":
    main()
