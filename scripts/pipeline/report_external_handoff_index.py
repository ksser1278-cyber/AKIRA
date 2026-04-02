from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from akira_engine.external_handoff_index import build_external_handoff_index, render_external_handoff_index
from akira_engine.reporting import write_utf8_json, write_utf8_text


def main() -> None:
    payload = build_external_handoff_index(PROJECT_ROOT)
    output_dir = PROJECT_ROOT / "reports" / "planning"
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "external_handoff_index.json"
    md_path = output_dir / "external_handoff_index.md"
    write_utf8_json(json_path, payload)
    write_utf8_text(md_path, render_external_handoff_index(payload), trailing_newline=False)
    print(str(json_path))
    print(str(md_path))


if __name__ == "__main__":
    main()
