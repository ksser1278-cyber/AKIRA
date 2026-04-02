from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import argparse
from pathlib import Path

from src.akira_engine.style_prompt_probe import build_style_prompt_mode_probes


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build mode-by-mode style prompt probes from an artist style_prompt_profile.json file.",
    )
    parser.add_argument(
        "--profile",
        required=True,
        type=Path,
        help="Path to artists/<artist_id>/style_prompt_profile.json",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs") / "style_prompt_probes",
        help="Directory where probe JSON and markdown files will be written.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    profile_path = args.profile.resolve()
    output_dir = args.output_dir if args.output_dir.is_absolute() else (Path.cwd() / args.output_dir).resolve()

    manifest = build_style_prompt_mode_probes(profile_path=profile_path, output_dir=output_dir)
    print(f"Manifest: {manifest['manifest_path']}")
    print(f"Mode count: {manifest['record_count']}")


if __name__ == "__main__":
    main()
