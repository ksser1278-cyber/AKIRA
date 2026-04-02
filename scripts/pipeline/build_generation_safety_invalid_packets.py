from __future__ import annotations

import json

from akira_engine.generation_safety_invalid_packet import build_generation_safety_packets
from akira_engine.generation_safety_invalid_queue import project_root


def main() -> None:
    root = project_root()
    payload = build_generation_safety_packets(root)
    print(root / "data" / "_global" / "generation_safety_invalid" / "manifest.json")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
