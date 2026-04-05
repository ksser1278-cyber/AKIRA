from __future__ import annotations

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from akira_engine.round2_expansion import materialize_round2_seed_scaffolds


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Materialize round2 draft seeds into conditioning scaffold files.")
    parser.add_argument("--project-root", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = materialize_round2_seed_scaffolds(args.project_root)
    print(f"created conditioning: {result['created_conditioning_count']}")
    print(f"updated queues: {result['updated_queue_count']}")


if __name__ == "__main__":
    main()
