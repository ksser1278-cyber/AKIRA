from __future__ import annotations

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from akira_engine.audio_enrichment import enrich_artist_records, load_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Enrich conditioning records with owned-audio measurements.")
    parser.add_argument("--artist-id", required=True, help="Artist or producer id")
    parser.add_argument("--audio-summary", default="reports/audio/audio_analysis_summary.json", help="Path to audio summary JSON")
    parser.add_argument("--project-root", default=".", help="Project root")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    project_root = Path(args.project_root).resolve()
    audio_summary_path = (project_root / args.audio_summary).resolve() if not Path(args.audio_summary).is_absolute() else Path(args.audio_summary)
    audio_summary = load_json(audio_summary_path)
    updated = enrich_artist_records(project_root, args.artist_id, audio_summary)
    print(f"Updated {len(updated)} conditioning records for {args.artist_id}")
    for path in updated:
        print(path)


if __name__ == "__main__":
    main()
