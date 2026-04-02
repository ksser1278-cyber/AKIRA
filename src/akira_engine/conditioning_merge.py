from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .reporting import write_utf8_json


REPLACE_LIST_PATHS = {
    "song_intent.narrative_role",
    "source_provenance.notes",
    "lyric_ground_truth.hook_lines",
    "lyric_ground_truth.question_lines",
    "lyric_ground_truth.repetition_patterns",
    "generation_safety.notes",
}


@dataclass
class ConditioningMergeResult:
    track_id: str
    target_path: str
    source_path: str
    changed: bool


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def deep_merge(base: Any, incoming: Any, path: str = "") -> Any:
    if isinstance(base, dict) and isinstance(incoming, dict):
        merged = dict(base)
        for key, value in incoming.items():
            child_path = f"{path}.{key}" if path else str(key)
            if key in merged:
                merged[key] = deep_merge(merged[key], value, child_path)
            else:
                merged[key] = value
        return merged
    if isinstance(base, list) and isinstance(incoming, list):
        if path in REPLACE_LIST_PATHS:
            return incoming
        if all(isinstance(item, dict) for item in base + incoming):
            return incoming
        merged: list[Any] = []
        seen: set[str] = set()
        for item in [*base, *incoming]:
            marker = json.dumps(item, ensure_ascii=False, sort_keys=True) if isinstance(item, (dict, list)) else str(item)
            if marker not in seen:
                seen.add(marker)
                merged.append(item)
        return merged
    return incoming


def raw_conditioning_filename(track_id: str, artist_id: str) -> str:
    clean_track_id = str(track_id).strip()
    prefix = f"{artist_id}_"
    if clean_track_id.startswith(prefix):
        clean_track_id = clean_track_id[len(prefix) :]
    return f"{clean_track_id}.conditioning.json"


def merge_external_conditioning_record(
    *,
    artist_id: str,
    target_dir: Path,
    source_path: Path,
    backup_dir: Path | None = None,
) -> ConditioningMergeResult:
    incoming = load_json(source_path)
    track_id = str(incoming.get("track_identity", {}).get("track_id") or incoming.get("track_id") or "").strip()
    if not track_id:
        raise ValueError(f"track_id missing in {source_path}")

    target_path = target_dir / raw_conditioning_filename(track_id, artist_id)
    if not target_path.exists():
        raise FileNotFoundError(f"Target conditioning not found for {track_id}: {target_path}")

    base = load_json(target_path)
    merged = deep_merge(base, incoming)
    changed = merged != base

    if changed and backup_dir is not None:
        backup_dir.mkdir(parents=True, exist_ok=True)
        write_utf8_json(backup_dir / target_path.name, base)
    if changed:
        write_utf8_json(target_path, merged)

    return ConditioningMergeResult(
        track_id=track_id,
        target_path=str(target_path),
        source_path=str(source_path),
        changed=changed,
    )
