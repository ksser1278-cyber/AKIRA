from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from akira_engine.expansion_queue import sync_expansion_queue_status


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync producer expansion queue statuses from conditioning audit grades.")
    parser.add_argument("--artist-id", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = sync_expansion_queue_status(PROJECT_ROOT, args.artist_id)
    print(result["queue_path"])
    print(f"changed={result['changed_count']} total={result['record_count']}")


if __name__ == "__main__":
    main()
