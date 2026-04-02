from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_mode_support_status(project_root: Path) -> dict[str, Any]:
    manifest = load_json(project_root / "data" / "anchor_sets" / "mode_support_set.json")
    output_root = project_root / "data" / "_global" / "mode_support"
    mode_rows: list[dict[str, Any]] = []

    for mode_block in manifest.get("modes", []):
        mode_id = str(mode_block.get("mode_id", "")).strip()
        if not mode_id:
            continue

        queue_path = output_root / mode_id / "queue.json"
        queue_payload = load_json(queue_path) if queue_path.exists() else {"queue": []}
        queue = queue_payload.get("queue", [])
        scaffolded_artists = sum(1 for item in queue if str(item.get("status", "")).strip() == "scaffolded")
        ready_artists = sum(1 for item in queue if str(item.get("status", "")).strip() == "ready_for_scaffold")
        pending_artists = sum(1 for item in queue if str(item.get("status", "")).strip() == "artist_curation_pending")
        track_targets = sum(int(item.get("target_track_count", 0) or 0) for item in queue)

        mode_rows.append(
            {
                "mode_id": mode_id,
                "target_count": int(mode_block.get("target_count", 0) or 0),
                "support_artists": [str(artist_id).strip() for artist_id in mode_block.get("support_artists", []) if str(artist_id).strip()],
                "artist_count": len(queue),
                "scaffolded_artist_count": scaffolded_artists,
                "ready_artist_count": ready_artists,
                "pending_artist_count": pending_artists,
                "queued_track_target": track_targets,
                "queue": queue,
            }
        )

    return {
        "schema_version": "1.0",
        "record_type": "mode_support_status",
        "modes": mode_rows,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = ["# Mode Support Status", ""]
    for mode in payload.get("modes", []):
        lines.append(f"## {mode['mode_id']}")
        lines.append("")
        lines.append(f"- target count `{mode['target_count']}`")
        lines.append(f"- support artists `{', '.join(mode.get('support_artists', []))}`")
        lines.append(f"- pending artist curation `{mode['pending_artist_count']}`")
        lines.append(f"- scaffolded `{mode['scaffolded_artist_count']}`")
        lines.append(f"- ready for scaffold `{mode['ready_artist_count']}`")
        lines.append(f"- queued track target `{mode['queued_track_target']}`")
        for item in mode.get("queue", []):
            lines.append(
                f"- `{item['artist_id']}` / status `{item['status']}` / target `{item['target_track_count']}`"
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
