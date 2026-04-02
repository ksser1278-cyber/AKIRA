from __future__ import annotations

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from akira_engine.round2_expansion import scaffold_round2_expansion


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build round2 expansion queues and seed scaffold files.")
    parser.add_argument("--project-root", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = scaffold_round2_expansion(args.project_root)
    print(f"registry: {result['registry_path']}")
    print(f"queues: {result['queue_count']}")
    print(f"seed files: {result['seed_file_count']}")


if __name__ == "__main__":
    main()
