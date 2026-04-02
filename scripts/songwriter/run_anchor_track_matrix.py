from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.akira_engine.anchor_matrix import run_anchor_matrix


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Songwriter V2 over all conditioning anchor tracks and build a score matrix.",
    )
    parser.add_argument(
        "--artist-id",
        required=True,
        help="Artist id, for example 'ado'.",
    )
    parser.add_argument(
        "--source-jsonl",
        required=True,
        type=Path,
        help="Path to full_song_brief JSONL.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("outputs") / "songwriter_v2_anchor_matrix",
        help="Root directory for anchor runs.",
    )
    parser.add_argument(
        "--candidate-count",
        type=int,
        default=12,
        help="Number of candidates to generate per anchor track.",
    )
    return parser.parse_args()

def main() -> None:
    args = parse_args()
    project_root = Path(__file__).resolve().parents[2]
    source_jsonl = args.source_jsonl.resolve()
    output_root = args.output_root if args.output_root.is_absolute() else (project_root / args.output_root).resolve()
    manifest = run_anchor_matrix(
        artist_id=args.artist_id,
        source_jsonl=source_jsonl,
        output_root=output_root,
        candidate_count=args.candidate_count,
        project_root=project_root,
    )
    print(manifest["manifest_path"])
    print(manifest["report_path"])


if __name__ == "__main__":
    main()
