from __future__ import annotations

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from akira_engine.mode_support_benchmark import run_mode_support_benchmark


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run benchmark over mode support tracks.")
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--mode-id", required=True)
    parser.add_argument("--output-root", default="outputs/mode_support_benchmark")
    parser.add_argument("--candidate-count", type=int, default=8)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    project_root = Path(args.project_root).resolve()
    output_root = Path(args.output_root)
    if not output_root.is_absolute():
        output_root = (project_root / output_root).resolve()
    manifest = run_mode_support_benchmark(
        project_root=project_root,
        mode_id=args.mode_id,
        output_root=output_root,
        candidate_count=args.candidate_count,
    )
    print(manifest["manifest_path"])
    print(manifest["report_path"])


if __name__ == "__main__":
    main()
