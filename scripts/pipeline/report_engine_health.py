from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from akira_engine.cli import run_report_engine_health


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
    result = run_report_engine_health(
        project_root=PROJECT_ROOT,
        artists=args.artists,
        output_dir=args.output_dir,
    )
    print(result["json_path"])
    print(result["md_path"])
    print(f"Source root: {result['source_root']}")


if __name__ == "__main__":
    main()
