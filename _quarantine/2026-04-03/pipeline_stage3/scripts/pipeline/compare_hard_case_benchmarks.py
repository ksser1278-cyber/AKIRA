from __future__ import annotations

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from akira_engine.hard_case_compare import write_hard_case_comparison


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare two hard-case benchmark manifests.")
    parser.add_argument("--baseline-manifest", required=True, type=Path)
    parser.add_argument("--candidate-manifest", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = args.output_dir if args.output_dir.is_absolute() else (PROJECT_ROOT / args.output_dir)
    payload = write_hard_case_comparison(
        baseline_manifest_path=args.baseline_manifest.resolve(),
        candidate_manifest_path=args.candidate_manifest.resolve(),
        output_dir=output_dir.resolve(),
    )
    print(payload["json_path"])
    print(payload["markdown_path"])


if __name__ == "__main__":
    main()
