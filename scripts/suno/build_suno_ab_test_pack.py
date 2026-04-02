from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import argparse
from pathlib import Path

from src.akira_engine.suno_ab import build_suno_ab_test_pack


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a Suno A/B test pack from bundle or probe JSON files.",
    )
    parser.add_argument(
        "--source-dir",
        required=True,
        type=Path,
        help="Directory containing Suno bundle or style prompt probe JSON files.",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        type=Path,
        help="Directory where the A/B test pack will be written.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    source_dir = args.source_dir.resolve()
    output_dir = args.output_dir if args.output_dir.is_absolute() else (Path.cwd() / args.output_dir).resolve()

    manifest = build_suno_ab_test_pack(source_dir=source_dir, output_dir=output_dir)
    print(f"Manifest: {manifest['manifest_path']}")
    print(f"Runbook: {manifest['runbook_path']}")
    print(f"Results template: {manifest['results_template_path']}")
    print(f"Pair count: {manifest['record_count']}")


if __name__ == "__main__":
    main()
