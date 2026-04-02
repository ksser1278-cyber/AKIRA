from __future__ import annotations

import json

from akira_engine.generation_safety_invalid_handoff import (
    build_invalid_handoff,
    project_root,
    render_invalid_delegation_prompt,
    render_invalid_handoff_markdown,
)


def main() -> None:
    root = project_root()
    payload = build_invalid_handoff(root)
    planning_dir = root / "reports" / "planning"
    (planning_dir / "generation_safety_invalid_handoff.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (planning_dir / "generation_safety_invalid_handoff.md").write_text(
        render_invalid_handoff_markdown(payload),
        encoding="utf-8",
    )
    (planning_dir / "generation_safety_invalid_delegation_prompt.txt").write_text(
        render_invalid_delegation_prompt(payload),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
