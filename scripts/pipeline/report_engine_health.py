from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from akira_engine.engine_health import build_engine_health, render_engine_health_markdown
from akira_engine.reporting import write_utf8_json, write_utf8_text


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build an engine health report across active artists.")
    parser.add_argument(
        "--artists",
        nargs="+",
        default=["pinocchiop", "deco27", "kanaria", "kairiki_bear", "maretu", "iyowa", "syudou", "neru"],
        help="Artist ids to include in the report.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("reports") / "health",
        help="Output directory for health artifacts.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    project_root = PROJECT_ROOT
    output_dir = args.output_dir if args.output_dir.is_absolute() else (project_root / args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    payload = build_engine_health(args.artists)
    json_path = output_dir / "engine_health.json"
    md_path = output_dir / "engine_health.md"
    write_utf8_json(json_path, payload)
    write_utf8_text(md_path, render_engine_health_markdown(payload), trailing_newline=False)
    print(str(json_path))
    print(str(md_path))


if __name__ == "__main__":
    main()
