from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_producer_expansion_status(project_root: Path) -> dict[str, Any]:
    manifest = load_json(project_root / "data" / "anchor_sets" / "producer_expansion_set.json")
    artists_payload: list[dict[str, Any]] = []

    for artist_block in manifest.get("artists", []):
        artist_id = str(artist_block.get("artist_id", "")).strip()
        if not artist_id:
            continue

        track_ids = [str(track_id).strip() for track_id in artist_block.get("track_ids", []) if str(track_id).strip()]
        reference_dir = project_root / "data" / artist_id / "reference_tracks"
        queue_path = reference_dir / "expansion_queue.json"
        queue_lookup: dict[str, dict[str, Any]] = {}
        if queue_path.exists():
            queue_payload = load_json(queue_path)
            queue_lookup = {
                str(item.get("track_id", "")).strip(): item
                for item in queue_payload.get("queue", [])
                if str(item.get("track_id", "")).strip()
            }

        track_rows: list[dict[str, Any]] = []
        scaffolded = 0
        queued = 0
        for track_id in track_ids:
            conditioning_path = reference_dir / f"{track_id.removeprefix(f'{artist_id}_')}.conditioning.json"
            has_scaffold = conditioning_path.exists()
            queue_item = queue_lookup.get(track_id, {})
            queue_status = str(queue_item.get("status", "")).strip()
            if has_scaffold:
                scaffolded += 1
            if queue_item:
                queued += 1
            track_rows.append(
                {
                    "track_id": track_id,
                    "has_conditioning_scaffold": has_scaffold,
                    "queue_status": queue_status or "missing",
                }
            )

        artists_payload.append(
            {
                "artist_id": artist_id,
                "total_tracks": len(track_ids),
                "scaffolded_tracks": scaffolded,
                "queued_tracks": queued,
                "tracks": track_rows,
            }
        )

    return {
        "schema_version": "1.0",
        "record_type": "producer_expansion_status",
        "artists": artists_payload,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = ["# Producer Expansion Status", ""]
    for artist in payload.get("artists", []):
        lines.append(f"## {artist['artist_id']}")
        lines.append("")
        lines.append(
            f"- scaffolded `{artist['scaffolded_tracks']}/{artist['total_tracks']}`"
        )
        lines.append(
            f"- queued `{artist['queued_tracks']}/{artist['total_tracks']}`"
        )
        for track in artist.get("tracks", []):
            scaffold = "yes" if track.get("has_conditioning_scaffold") else "no"
            lines.append(
                f"- `{track['track_id']}` / scaffold `{scaffold}` / queue `{track['queue_status']}`"
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
