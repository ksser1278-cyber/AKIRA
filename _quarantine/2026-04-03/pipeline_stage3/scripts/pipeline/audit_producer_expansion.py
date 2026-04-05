from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from akira_engine.conditioning_audit import audit_conditioning_paths, render_audit_markdown


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit producer expansion conditioning records for an artist.")
    parser.add_argument("--artist-id", required=True)
    parser.add_argument("--project-root", default=".")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    project_root = Path(args.project_root).resolve()
    artist_dir = project_root / "data" / args.artist_id / "reference_tracks"
    queue_path = artist_dir / "expansion_queue.json"
    queue = json.loads(queue_path.read_text(encoding="utf-8"))
    paths: list[Path] = []
    missing: list[str] = []
    for item in queue.get("queue", []):
        track_id = str(item.get("track_id", "")).strip()
        if not track_id:
            continue
        candidate = artist_dir / f"{track_id.removeprefix(f'{args.artist_id}_')}.conditioning.json"
        if candidate.exists():
            paths.append(candidate)
        else:
            missing.append(str(candidate))
    if missing:
        raise SystemExit("Missing producer expansion conditioning files:\n" + "\n".join(missing))

    summary = audit_conditioning_paths(paths, args.artist_id)
    output_dir = project_root / "reports" / "quality" / "conditioning"
    json_path = output_dir / f"{args.artist_id}_producer_expansion_audit.json"
    md_path = output_dir / f"{args.artist_id}_producer_expansion_audit.md"
    json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(render_audit_markdown(summary), encoding="utf-8")
    print(json_path)
    print(md_path)


if __name__ == "__main__":
    main()
