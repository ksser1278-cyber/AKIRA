from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from akira_engine.mode_support import load_json, write_json
from akira_engine.reporting import write_utf8_json, write_utf8_text


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Merge mode support curation payloads into mode support queue.")
    parser.add_argument("--mode-id", required=True)
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--project-root", default=".")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    project_root = Path(args.project_root).resolve()
    input_dir = Path(args.input_dir).resolve()
    queue_path = project_root / "data" / "_global" / "mode_support" / args.mode_id / "queue.json"
    queue = load_json(queue_path)

    merged = []
    artist_map = {str(item.get("artist_id", "")).strip(): item for item in queue.get("queue", [])}
    for path in sorted(input_dir.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        for item in payload.get("artist_candidates", []):
            artist_id = str(item.get("artist_id", "")).strip()
            if not artist_id or artist_id not in artist_map:
                continue
            target = artist_map[artist_id]
            target["candidate_track_ids"] = [str(track_id).strip() for track_id in item.get("candidate_track_ids", []) if str(track_id).strip()]
            target["candidate_titles"] = [str(title).strip() for title in item.get("candidate_titles", []) if str(title).strip()]
            target["notes"] = [str(note).strip() for note in item.get("notes", []) if str(note).strip()]
            if target["candidate_track_ids"]:
                target["status"] = "ready_for_scaffold"
            merged.append({"artist_id": artist_id, "filename": path.name, "candidate_count": len(target["candidate_track_ids"])})

    write_json(queue_path, queue)

    output = {
        "schema_version": "1.0",
        "mode_id": args.mode_id,
        "input_dir": str(input_dir),
        "queue_path": str(queue_path),
        "merged_count": len(merged),
        "merged": merged,
    }
    out_dir = project_root / "reports" / "quality" / "mode_support_merge"
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"{args.mode_id}_mode_support_merge.json"
    md_path = out_dir / f"{args.mode_id}_mode_support_merge.md"
    write_utf8_json(json_path, output)
    write_utf8_text(
        md_path,
        "\n".join(
            [
                f"# Mode Support Merge: {args.mode_id}",
                "",
                f"- Merged entries: `{len(merged)}`",
                f"- Queue: `{queue_path}`",
                "",
            ]
            + [f"- `{item['artist_id']}` / `{item['candidate_count']}` candidates / from `{item['filename']}`" for item in merged]
        ),
        trailing_newline=False,
    )
    print(json_path)
    print(md_path)


if __name__ == "__main__":
    main()
