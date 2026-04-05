from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from akira_engine.generation_safety import (
    apply_generation_safety_pilot,
    project_root,
    render_generation_safety_pilot_markdown,
    save_json,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Apply generation_safety pilot verdicts to target conditioning records.")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Recompute generation_safety for records that already have the field.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = project_root()
    payload = apply_generation_safety_pilot(root, overwrite=args.overwrite)
    planning_dir = root / "reports" / "planning"
    save_json(planning_dir / "generation_safety_pilot_status.json", payload)
    (planning_dir / "generation_safety_pilot_status.md").write_text(
        render_generation_safety_pilot_markdown(payload),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
