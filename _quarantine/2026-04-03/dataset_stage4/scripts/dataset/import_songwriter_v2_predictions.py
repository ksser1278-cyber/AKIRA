from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import argparse
from pathlib import Path

from src.akira_engine.songwriter_v2_exchange import import_prediction_bundle, render_import_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Import model prediction JSONL into markdown files for Songwriter V2 scoring.",
    )
    parser.add_argument(
        "--input-jsonl",
        required=True,
        type=Path,
        help="JSONL file containing track_id and markdown output fields.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs") / "songwriter_v2_imported_predictions",
        help="Directory where markdown prediction files will be written.",
    )
    parser.add_argument(
        "--report",
        type=Path,
        help="Optional markdown report path.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_jsonl = args.input_jsonl.resolve()
    output_dir = args.output_dir if args.output_dir.is_absolute() else (Path.cwd() / args.output_dir).resolve()

    manifest = import_prediction_bundle(input_jsonl, output_dir)

    report_path = args.report or (output_dir / "import_report.md")
    final_report_path = report_path if report_path.is_absolute() else (Path.cwd() / report_path).resolve()
    final_report_path.parent.mkdir(parents=True, exist_ok=True)
    final_report_path.write_text(render_import_report(manifest), encoding="utf-8")

    print(f"Import manifest: {manifest['manifest_path']}")
    print(f"Import report: {final_report_path}")
    print(f"Written markdown files: {manifest['written_count']}")


if __name__ == "__main__":
    main()
