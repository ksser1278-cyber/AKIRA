from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import argparse
from pathlib import Path

from src.akira_engine.generator import GenerationRequest, generate_package


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a SUNO prompt package from a structured artist profile."
    )
    parser.add_argument(
        "--artist",
        required=True,
        type=Path,
        help="Path to the artist profile JSON file.",
    )
    parser.add_argument(
        "--mode",
        required=True,
        help="Mode identifier from the artist profile.",
    )
    parser.add_argument(
        "--theme",
        required=True,
        help="High-level song topic or conflict.",
    )
    parser.add_argument(
        "--emotion",
        required=True,
        help="Dominant emotion for the package.",
    )
    parser.add_argument(
        "--narrative",
        required=True,
        help="One-sentence narrative direction for the lyric plan.",
    )
    parser.add_argument(
        "--keyword",
        action="append",
        default=[],
        help="Optional keyword anchor. Repeat the flag to add more keywords.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional output markdown path. Defaults to outputs/<artist>_<mode>_<theme>.md",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    request = GenerationRequest(
        artist_file=args.artist,
        mode_id=args.mode,
        theme=args.theme,
        emotion=args.emotion,
        narrative=args.narrative,
        keywords=args.keyword,
        output_path=args.output,
    )
    output_path = generate_package(request)
    print(f"Generated: {output_path}")


if __name__ == "__main__":
    main()
