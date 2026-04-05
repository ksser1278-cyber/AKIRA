from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import argparse
from pathlib import Path

from src.akira_engine.lyric_draft import LyricDraftRequest, generate_lyric_draft


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a safe original lyric draft from a brief JSONL record.",
    )
    parser.add_argument(
        "--source-jsonl",
        required=True,
        type=Path,
        help="JSONL file containing full_song_brief or full_song_brief_eval records.",
    )
    parser.add_argument(
        "--track-id",
        help="Optional track_id to select a specific record. Defaults to the first record.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional markdown output path.",
    )
    parser.add_argument(
        "--candidate-count",
        type=int,
        default=6,
        help="Number of draft variants to sample before selecting the best candidate.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_path = generate_lyric_draft(
        LyricDraftRequest(
            source_jsonl=args.source_jsonl,
            track_id=args.track_id,
            output_path=args.output,
            candidate_count=args.candidate_count,
        )
    )
    print(f"Lyric draft: {output_path}")


if __name__ == "__main__":
    main()
