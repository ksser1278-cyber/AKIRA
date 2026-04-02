from __future__ import annotations

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from akira_engine.round2_expansion import load_json, sync_round2_queue_status


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync round2 queue statuses from round2 audits.")
    parser.add_argument("--project-root", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    registry = load_json(args.project_root / "data" / "_global" / "round2_expansion" / "registry.json")
    for artist in registry.get("artists", []):
        artist_id = str(artist.get("artist_id", "")).strip()
        if not artist_id:
            continue
        result = sync_round2_queue_status(args.project_root, artist_id)
        print(f"{artist_id}: changed {result['changed_count']} / {result['record_count']}")


if __name__ == "__main__":
    main()
