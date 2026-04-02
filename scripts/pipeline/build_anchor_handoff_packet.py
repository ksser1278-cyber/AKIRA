from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from akira_engine.anchor_handoff_packet import write_anchor_handoff_packet


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build anchor handoff packet.")
    parser.add_argument("--artist-id", required=True)
    parser.add_argument("--project-root", default=".")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    project_root = Path(args.project_root).resolve()
    output_path = write_anchor_handoff_packet(project_root, args.artist_id)
    print(output_path)


if __name__ == "__main__":
    main()
