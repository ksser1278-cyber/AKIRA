from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .conditioning_audit import audit_conditioning_paths


def _slug_title(track_id: str, artist_id: str) -> str:
    slug = track_id.removeprefix(f"{artist_id}_").replace("_", " ").strip()
    return " ".join(part.capitalize() for part in slug.split())


def _prefer_ascii_title(value: str, fallback: str) -> str:
    text = value.strip()
    if text and text.isascii():
        return text
    return fallback


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_expansion_queue(project_root: Path, artist_id: str) -> dict[str, Any]:
    producer_expansion = load_json(project_root / "data" / "anchor_sets" / "producer_expansion_set.json")
    active_queue = load_json(project_root / "data" / artist_id / "reference_tracks" / "conditioning_queue.json")
    reference_dir = project_root / "data" / artist_id / "reference_tracks"

    expansion_ids: list[str] = []
    for block in producer_expansion.get("artists", []):
        if str(block.get("artist_id", "")).strip() == artist_id:
            expansion_ids = [str(track_id).strip() for track_id in block.get("track_ids", []) if str(track_id).strip()]
            break

    active_lookup = {
        str(item.get("track_id", "")).strip(): item
        for item in active_queue.get("queue", [])
        if str(item.get("track_id", "")).strip()
    }

    queue_items: list[dict[str, Any]] = []
    for priority, track_id in enumerate(expansion_ids, start=1):
        item = active_lookup.get(track_id)
        title = ""
        romanized = ""
        mode = "unknown"
        status = "pending"
        slug_title = _slug_title(track_id, artist_id)
        conditioning_path = reference_dir / (track_id.removeprefix(f"{artist_id}_") + ".conditioning.json")
        conditioning_payload: dict[str, Any] = {}
        if conditioning_path.exists():
            conditioning_payload = load_json(conditioning_path)
        identity = conditioning_payload.get("track_identity", {})
        conditioning_title = str(identity.get("title", "")).strip()
        conditioning_core = str(identity.get("title_core", "")).strip()
        if item:
            title = str(item.get("title", "")).strip()
            romanized = str(item.get("romanized", "")).strip()
            mode = str(item.get("mode", "")).strip() or mode
            status = str(item.get("status", "")).strip() or status
        if conditioning_payload:
            if not title:
                title = conditioning_title
            if not romanized:
                romanized = conditioning_core
            mode_list = conditioning_payload.get("song_intent", {}).get("narrative_role", [])
            if isinstance(mode_list, list) and mode_list:
                mode = str(mode_list[0]).strip() or mode
            if not item:
                status = "drafted"

        if conditioning_core:
            romanized = conditioning_core
            if not title:
                title = conditioning_core
        elif conditioning_title and not title:
            title = conditioning_title

        romanized = _prefer_ascii_title(romanized, slug_title)
        title = _prefer_ascii_title(title, romanized or slug_title)

        queue_items.append(
            {
                "priority": priority,
                "track_id": track_id,
                "title": title,
                "romanized": romanized,
                "mode": mode,
                "status": status,
                "required_inputs": [
                    "lyrics",
                    "credits",
                    "release year",
                    "hook lines",
                    "section map",
                    "prompt conditioning",
                ],
            }
        )

    return {
        "schema_version": "1.0",
        "artist_id": artist_id,
        "reference_role": "producer expansion queue",
        "queue": queue_items,
    }


def sync_expansion_queue_status(project_root: Path, artist_id: str) -> dict[str, Any]:
    queue_path = project_root / "data" / artist_id / "reference_tracks" / "expansion_queue.json"
    queue_payload = load_json(queue_path)
    reference_dir = project_root / "data" / artist_id / "reference_tracks"

    path_lookup: dict[str, Path] = {}
    for item in queue_payload.get("queue", []):
        track_id = str(item.get("track_id", "")).strip()
        if not track_id:
            continue
        path_lookup[track_id] = reference_dir / f"{track_id.removeprefix(f'{artist_id}_')}.conditioning.json"

    audited_paths = [path for path in path_lookup.values() if path.exists()]
    audit_lookup: dict[str, dict[str, Any]] = {}
    if audited_paths:
        audit_summary = audit_conditioning_paths(audited_paths, artist_id)
        audit_lookup = {
            str(record.get("track_id", "")).strip(): record
            for record in audit_summary.get("records", [])
            if str(record.get("track_id", "")).strip()
        }

    changed = 0
    for item in queue_payload.get("queue", []):
        track_id = str(item.get("track_id", "")).strip()
        current_status = str(item.get("status", "")).strip() or "pending"
        next_status = current_status
        record = audit_lookup.get(track_id)
        if record:
            grade = str(record.get("grade", "")).strip()
            if grade == "gold":
                next_status = "validated"
            elif grade == "usable":
                next_status = "drafted"
            else:
                next_status = "scaffolded"
        elif path_lookup.get(track_id, Path()).exists():
            next_status = "scaffolded"
        else:
            next_status = "pending"
        if next_status != current_status:
            item["status"] = next_status
            changed += 1

    write_json(queue_path, queue_payload)
    return {
        "artist_id": artist_id,
        "queue_path": str(queue_path),
        "changed_count": changed,
        "record_count": len(queue_payload.get("queue", [])),
    }
