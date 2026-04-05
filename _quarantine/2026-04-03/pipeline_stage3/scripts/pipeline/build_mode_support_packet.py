from __future__ import annotations

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from akira_engine.mode_support import load_json
from akira_engine.mode_support_packet import write_mode_support_packet


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build mode support external handoff packets.")
    parser.add_argument("--project-root", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest = load_json(args.project_root / "data" / "anchor_sets" / "mode_support_set.json")
    for mode_block in manifest.get("modes", []):
        mode_id = str(mode_block.get("mode_id", "")).strip()
        if not mode_id:
            continue
        prompt_path, packet_path = write_mode_support_packet(args.project_root, mode_id)
        print(prompt_path)
        print(packet_path)


if __name__ == "__main__":
    main()
