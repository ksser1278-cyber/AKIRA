from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from akira_engine.reporting import write_utf8_text
from akira_engine.round2_upgrade_overview import (
    build_round2_upgrade_overview,
    render_round2_upgrade_overview_markdown,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Report round2 upgrade overview.")
    parser.add_argument("--project-root", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = build_round2_upgrade_overview(args.project_root)
    out_dir = args.project_root / "reports" / "planning"
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "round2_upgrade_overview.json"
    md_path = out_dir / "round2_upgrade_overview.md"
    write_utf8_text(json_path, json.dumps(payload, ensure_ascii=False, indent=2))
    write_utf8_text(md_path, render_round2_upgrade_overview_markdown(payload))
    print(json_path)
    print(md_path)


if __name__ == "__main__":
    main()
