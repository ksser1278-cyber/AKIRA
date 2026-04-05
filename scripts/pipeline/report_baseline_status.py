from __future__ import annotations

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from akira_engine.cli import run_report_baseline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render current frozen baseline status.")
    parser.add_argument("--project-root", type=Path, default=PROJECT_ROOT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = run_report_baseline(
        project_root=args.project_root.resolve(),
    )
    print(result["data_path"])
    print(result["json_path"])
    print(result["md_path"])
    print(f"Source root: {result['source_root']}")


if __name__ == "__main__":
    main()
