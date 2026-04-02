from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from akira_engine.expansion_queue import build_expansion_queue, write_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build producer expansion queue for an artist.")
    parser.add_argument("--artist-id", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = build_expansion_queue(PROJECT_ROOT, args.artist_id)
    output_path = PROJECT_ROOT / "data" / args.artist_id / "reference_tracks" / "expansion_queue.json"
    write_json(output_path, payload)
    print(str(output_path))


if __name__ == "__main__":
    main()
