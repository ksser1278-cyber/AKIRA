from __future__ import annotations

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from akira_engine.round2_upgrade_batch_prompt import write_round2_upgrade_batch_prompt


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build round2 batch delegation prompt.")
    parser.add_argument("--project-root", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print(write_round2_upgrade_batch_prompt(args.project_root))


if __name__ == "__main__":
    main()
