from __future__ import annotations

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from akira_engine.mode_support import scaffold_mode_support


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build mode support scaffold queues and handoff directories.")
    parser.add_argument("--project-root", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    created = scaffold_mode_support(args.project_root)
    print(f"mode support scaffold complete: created {len(created)} queue files")
    for path in created:
        print(path)


if __name__ == "__main__":
    main()
