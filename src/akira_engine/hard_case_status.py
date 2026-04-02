from __future__ import annotations

from pathlib import Path
from typing import Any

from .hard_case import load_json


def build_hard_case_status(project_root: Path) -> dict[str, Any]:
    registry = load_json(project_root / "data" / "_global" / "hard_case_registry.json")
    artists_payload: list[dict[str, Any]] = []
    for artist in registry.get("artists", []):
        tracks = artist.get("tracks", [])
        open_count = sum(1 for item in tracks if str(item.get("status", "")).strip() == "open")
        resolved_count = sum(1 for item in tracks if str(item.get("status", "")).strip() == "resolved")
        deferred_count = sum(1 for item in tracks if str(item.get("status", "")).strip() == "deferred")
        artists_payload.append(
            {
                "artist_id": str(artist.get("artist_id", "")).strip(),
                "open_count": open_count,
                "resolved_count": resolved_count,
                "deferred_count": deferred_count,
                "tracks": tracks,
            }
        )
    return {
        "schema_version": "1.0",
        "record_type": "hard_case_status",
        "artists": artists_payload,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = ["# Hard Case Status", ""]
    for artist in payload.get("artists", []):
        lines.append(f"## {artist['artist_id']}")
        lines.append("")
        lines.append(f"- open `{artist['open_count']}`")
        lines.append(f"- resolved `{artist.get('resolved_count', 0)}`")
        lines.append(f"- deferred `{artist.get('deferred_count', 0)}`")
        for item in artist.get("tracks", []):
            reason = str(item.get("deferred_reason", "")).strip()
            resolution = str(item.get("resolution_note", "")).strip()
            suffix = ""
            if reason:
                suffix = f" / deferred `{reason}`"
            elif resolution:
                suffix = f" / resolved `{resolution}`"
            lines.append(
                f"- `{item['track_id']}` / selected `{item['score']}` / current `{item.get('current_best_score', 0.0)}` / `{item['status']}` / {'; '.join(item.get('issues', []))}{suffix}"
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
