from __future__ import annotations

import json

from akira_engine.generation_safety_invalid_queue import (
    build_invalid_queue,
    project_root,
    render_invalid_queue_markdown,
)


def main() -> None:
    root = project_root()
    payload = build_invalid_queue(root)
    planning_dir = root / "reports" / "planning"
    (planning_dir / "generation_safety_invalid_queue.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (planning_dir / "generation_safety_invalid_queue.md").write_text(
        render_invalid_queue_markdown(payload),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
