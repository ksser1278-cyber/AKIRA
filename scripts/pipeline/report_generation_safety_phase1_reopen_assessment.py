from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from akira_engine.generation_safety_phase1_reopen import write_phase1_reopen_outputs


def main() -> None:
    paths = write_phase1_reopen_outputs(PROJECT_ROOT)
    for path in paths.values():
        print(path)


if __name__ == "__main__":
    main()
