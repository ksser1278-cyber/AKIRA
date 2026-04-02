from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import argparse
from pathlib import Path

from src.akira_engine.profile_builder import derive_profile


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Derive a draft artist profile from an artist lyric analysis JSON."
    )
    parser.add_argument(
        "--analysis",
        required=True,
        type=Path,
        help="Path to an artist lyric analysis JSON file.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional output path. Defaults to artists/<artist_id>/profile.generated.json",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_path = derive_profile(args.analysis, args.output)
    print(f"Generated draft profile: {output_path}")


if __name__ == "__main__":
    main()
