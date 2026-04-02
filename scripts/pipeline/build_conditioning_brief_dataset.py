from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.akira_engine.conditioning_brief_dataset import (
    build_briefs_from_conditioning_paths,
    load_active_queue_records,
)


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def main() -> None:
    parser = argparse.ArgumentParser(description="Build full_song_brief JSONL from conditioning records.")
    parser.add_argument("--artist-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    reference_dir = project_root() / "data" / args.artist_id / "reference_tracks"
    records = build_briefs_from_conditioning_paths(load_active_queue_records(reference_dir, args.artist_id))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"Wrote {len(records)} records to {args.output}")


if __name__ == "__main__":
    main()
