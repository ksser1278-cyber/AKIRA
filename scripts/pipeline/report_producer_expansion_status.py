from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from akira_engine.producer_expansion_status import build_producer_expansion_status, render_markdown
from akira_engine.reporting import write_utf8_json, write_utf8_text


def main() -> None:
    payload = build_producer_expansion_status(PROJECT_ROOT)
    report_dir = PROJECT_ROOT / "reports" / "planning"
    json_path = report_dir / "producer_expansion_status.json"
    md_path = report_dir / "producer_expansion_status.md"
    write_utf8_json(json_path, payload)
    write_utf8_text(md_path, render_markdown(payload))
    print(str(json_path))
    print(str(md_path))


if __name__ == "__main__":
    main()
