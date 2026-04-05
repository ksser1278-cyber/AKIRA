from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import argparse
from pathlib import Path

from src.akira_engine.corpus import build_corpus, dataset_files_from_directory


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Merge per-artist lyric blueprint datasets into one corpus and manifest."
    )
    parser.add_argument(
        "--datasets-root",
        type=Path,
        default=Path("datasets") / "processed",
        help="Directory containing per-artist JSONL dataset files.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional merged corpus JSONL path.",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        help="Optional manifest JSON path.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    dataset_paths = dataset_files_from_directory(args.datasets_root)
    if not dataset_paths:
        raise SystemExit(f"No dataset files found in {args.datasets_root}")

    summary = build_corpus(
        dataset_paths=dataset_paths,
        corpus_path=args.output,
        manifest_path=args.manifest,
    )
    print(f"Generated corpus: {summary.corpus_path}")
    print(f"Generated manifest: {summary.manifest_path}")
    print(f"Total records: {summary.total_records}")
    print(f"Unique artists: {summary.unique_artists}")
    print(f"Split counts: {summary.split_counts}")


if __name__ == "__main__":
    main()
