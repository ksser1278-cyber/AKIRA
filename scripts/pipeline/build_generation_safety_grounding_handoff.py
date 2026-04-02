from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from akira_engine.generation_safety_grounding_handoff import write_grounding_handoff


def main() -> None:
    write_grounding_handoff(PROJECT_ROOT)


if __name__ == "__main__":
    main()
