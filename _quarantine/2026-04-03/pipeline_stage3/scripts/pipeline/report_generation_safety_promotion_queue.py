from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from akira_engine.generation_safety_promotion_queue import (
    build_promotion_queue,
    project_root,
    render_promotion_queue_markdown,
)


def main() -> None:
    root = project_root()
    payload = build_promotion_queue(root)
    planning_dir = root / "reports" / "planning"
    (planning_dir / "generation_safety_promotion_queue.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (planning_dir / "generation_safety_promotion_queue.md").write_text(
        render_promotion_queue_markdown(payload),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
