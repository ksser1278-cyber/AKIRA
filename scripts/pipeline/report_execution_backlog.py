from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from akira_engine.execution_backlog import build_execution_backlog, render_execution_backlog_markdown
from akira_engine.reporting import write_utf8_json, write_utf8_text


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build execution backlog from health and dataset manifests.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("reports") / "planning",
        help="Output directory for backlog artifacts.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = args.output_dir if args.output_dir.is_absolute() else (PROJECT_ROOT / args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    payload = build_execution_backlog()
    json_path = output_dir / "execution_backlog.json"
    md_path = output_dir / "execution_backlog.md"
    write_utf8_json(json_path, payload)
    write_utf8_text(md_path, render_execution_backlog_markdown(payload), trailing_newline=False)
    print(str(json_path))
    print(str(md_path))


if __name__ == "__main__":
    main()
