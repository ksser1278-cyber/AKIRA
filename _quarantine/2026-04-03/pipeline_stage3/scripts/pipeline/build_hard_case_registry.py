from __future__ import annotations

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from akira_engine.hard_case import build_hard_case_registry, write_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build hard case registry from current health.")
    parser.add_argument("--project-root", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = build_hard_case_registry(args.project_root)
    path = args.project_root / "data" / "_global" / "hard_case_registry.json"
    write_json(path, payload)
    print(path)


if __name__ == "__main__":
    main()
