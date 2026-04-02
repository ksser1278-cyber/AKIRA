from __future__ import annotations

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from akira_engine.conditioning_scaffold import scaffold_from_audio_summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create draft conditioning records from owned-audio summary.")
    parser.add_argument("--artist-id", required=True)
    parser.add_argument("--track-id", action="append", dest="track_ids", required=True)
    parser.add_argument("--project-root", default=".")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    project_root = Path(args.project_root).resolve()
    created = scaffold_from_audio_summary(project_root, args.artist_id, args.track_ids)
    print(f"Created {len(created)} conditioning records")
    for path in created:
        print(path)


if __name__ == "__main__":
    main()
