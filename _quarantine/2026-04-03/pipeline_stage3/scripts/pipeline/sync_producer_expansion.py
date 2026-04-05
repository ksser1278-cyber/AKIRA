from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from akira_engine.producer_expansion import scaffold_from_queue, sync_producer_expansion_set


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync producer expansion set and scaffold pending queue tracks.")
    parser.add_argument(
        "--artists",
        nargs="+",
        default=["pinocchiop", "deco27"],
        help="Artist ids to scaffold from queue.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    sync_result = sync_producer_expansion_set(PROJECT_ROOT)
    scaffold_results = {
        artist_id: scaffold_from_queue(PROJECT_ROOT, artist_id)
        for artist_id in args.artists
    }
    print(
        json.dumps(
            {
                "sync_result": sync_result,
                "scaffold_results": scaffold_results,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
