from __future__ import annotations

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from akira_engine.baseline_status import build_baseline_status, render_baseline_status_markdown
from akira_engine.reporting import write_utf8_json, write_utf8_text


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render current frozen baseline status.")
    parser.add_argument("--project-root", type=Path, default=PROJECT_ROOT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    project_root = args.project_root.resolve()
    payload = build_baseline_status(project_root)

    data_path = project_root / "data" / "baseline_registry.json"
    report_dir = project_root / "reports" / "planning"
    report_dir.mkdir(parents=True, exist_ok=True)

    write_utf8_json(data_path, payload)
    write_utf8_json(report_dir / "baseline_status.json", payload)
    write_utf8_text(report_dir / "baseline_status.md", render_baseline_status_markdown(payload))

    print(str(data_path))
    print(str(report_dir / "baseline_status.json"))
    print(str(report_dir / "baseline_status.md"))


if __name__ == "__main__":
    main()
