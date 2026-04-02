from __future__ import annotations

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from akira_engine.hard_case_benchmark import run_hard_case_benchmark


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run benchmark only for current hard-case tracks.")
    parser.add_argument("--artist-id", required=True)
    parser.add_argument("--source-jsonl", required=True, type=Path)
    parser.add_argument("--output-root", type=Path, default=Path("outputs") / "hard_case_benchmark")
    parser.add_argument("--candidate-count", type=int, default=12)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_root = args.output_root if args.output_root.is_absolute() else (PROJECT_ROOT / args.output_root)
    manifest = run_hard_case_benchmark(
        project_root=PROJECT_ROOT,
        artist_id=args.artist_id,
        source_jsonl=args.source_jsonl.resolve(),
        output_root=output_root.resolve(),
        candidate_count=args.candidate_count,
    )
    print(manifest["manifest_path"])
    print(manifest["report_path"])


if __name__ == "__main__":
    main()
