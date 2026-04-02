from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from akira_engine.conditioning_audit import (
    audit_artist_conditioning,
    audit_conditioning_paths,
    render_audit_markdown,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit conditioning records for trust and completeness.")
    parser.add_argument("--artist-id", required=True, help="Artist or producer id, e.g. pinocchiop")
    parser.add_argument("--project-root", default=".", help="Project root path")
    parser.add_argument(
        "--active-queue-only",
        action="store_true",
        help="Audit only the tracks listed in reference_tracks/conditioning_queue.json",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    project_root = Path(args.project_root).resolve()
    artist_dir = project_root / "data" / args.artist_id / "reference_tracks"
    if not artist_dir.exists():
        raise SystemExit(f"Conditioning directory not found: {artist_dir}")

    if args.active_queue_only:
        queue_path = artist_dir / "conditioning_queue.json"
        if not queue_path.exists():
            raise SystemExit(f"conditioning_queue.json not found: {queue_path}")
        queue_record = json.loads(queue_path.read_text(encoding="utf-8"))
        active_paths: list[Path] = []
        missing_paths: list[str] = []
        for item in queue_record.get("queue", []):
            status = str(item.get("status", "")).strip().lower()
            if status == "pending":
                continue
            track_id = item.get("track_id", "").strip()
            if not track_id:
                continue
            raw_id = track_id.removeprefix(f"{args.artist_id}_")
            candidate_path = artist_dir / f"{raw_id}.conditioning.json"
            if candidate_path.exists():
                active_paths.append(candidate_path)
            else:
                missing_paths.append(str(candidate_path))
        if missing_paths:
            raise SystemExit("Missing queue conditioning files:\n" + "\n".join(missing_paths))
        summary = audit_conditioning_paths(active_paths, args.artist_id)
    else:
        summary = audit_artist_conditioning(artist_dir)
    output_dir = project_root / "reports" / "quality" / "conditioning"
    output_dir.mkdir(parents=True, exist_ok=True)

    suffix = "_active" if args.active_queue_only else ""
    json_path = output_dir / f"{args.artist_id}_conditioning_audit{suffix}.json"
    md_path = output_dir / f"{args.artist_id}_conditioning_audit{suffix}.md"

    json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(render_audit_markdown(summary), encoding="utf-8")

    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")


if __name__ == "__main__":
    main()
