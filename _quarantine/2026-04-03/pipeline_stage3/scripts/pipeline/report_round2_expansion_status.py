from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from akira_engine.round2_expansion_status import build_round2_status, render_round2_status_markdown


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Report round2 expansion scaffold status.")
    parser.add_argument("--project-root", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    status = build_round2_status(args.project_root)
    report_dir = args.project_root / "reports" / "planning"
    report_dir.mkdir(parents=True, exist_ok=True)
    json_path = report_dir / "round2_expansion_status.json"
    md_path = report_dir / "round2_expansion_status.md"
    json_path.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_round2_status_markdown(status), encoding="utf-8")
    print(str(md_path))


if __name__ == "__main__":
    main()
