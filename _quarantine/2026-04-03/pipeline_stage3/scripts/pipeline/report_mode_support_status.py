from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from akira_engine.mode_support_status import build_mode_support_status, render_markdown
from akira_engine.reporting import write_utf8_text


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render mode support dataset status.")
    parser.add_argument("--project-root", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = build_mode_support_status(args.project_root)
    report_dir = args.project_root / "reports" / "planning"
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "mode_support_status.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_utf8_text(report_dir / "mode_support_status.md", render_markdown(payload))
    print(report_dir / "mode_support_status.md")


if __name__ == "__main__":
    main()
