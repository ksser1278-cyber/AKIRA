from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .training_data import write_json


def _safe_text(value: Any) -> str:
    return str(value or "").strip()


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _priority_score(record: dict[str, Any]) -> int:
    score = 0
    track = record.get("track_identity", {})
    meta = record.get("metadata_context", {})
    sources = record.get("acquisition_sources", {})
    title = _safe_text(track.get("canonical_title"))
    platform = _safe_text(meta.get("original_platform"))
    uploads = sources.get("official_uploads", [])
    if title:
        score += 3
    if platform in {"youtube", "niconico"}:
        score += 3
    elif platform == "other":
        score += 1
    if any("youtu" in url for url in uploads):
        score += 2
    if any("nicovideo" in url for url in uploads):
        score += 2
    if _safe_text(meta.get("engine_family")) in {"vocaloid", "utau", "cevio", "synthesizer_v"}:
        score += 1
    return score


def _is_grounding_deferred(record: dict[str, Any]) -> bool:
    title = _safe_text(record.get("track_identity", {}).get("canonical_title")).lower()
    producer = _safe_text(record.get("metadata_context", {}).get("producer")).lower()
    deferred_markers = (
        "デモソング",
        "試聴版",
        "demo song",
        "preview",
        "crossfade",
    )
    if any(marker.lower() in title for marker in deferred_markers):
        return True
    if "synthesizer v" in title and ("demo" in title or "試聴" in title):
        return True
    if "demo" in producer:
        return True
    return False


def build_lyric_technique_pilot_batch(
    *,
    queue_root: Path,
    output_root: Path,
    batch_size: int = 10,
    exclude_track_ids: list[str] | None = None,
) -> dict[str, Any]:
    queue_root = queue_root.resolve()
    output_root = output_root.resolve()
    records_dir = queue_root / "records"
    output_root.mkdir(parents=True, exist_ok=True)
    excluded = {track_id.strip() for track_id in (exclude_track_ids or []) if str(track_id).strip()}

    candidates: list[dict[str, Any]] = []
    for path in sorted(records_dir.glob("vocadb_*.json")):
        record = _load_json(path)
        track_id = _safe_text(record.get("track_identity", {}).get("track_id"))
        if track_id in excluded:
            continue
        if _is_grounding_deferred(record):
            continue
        queue_status = record.get("queue_status", {})
        if not bool(queue_status.get("ready_for_lyric_grounding")):
            continue
        candidates.append(record)

    candidates.sort(
        key=lambda record: (
            -_priority_score(record),
            _safe_text(record.get("metadata_context", {}).get("original_upload_date")),
            _safe_text(record.get("track_identity", {}).get("track_id")),
        )
    )
    selected = candidates[:batch_size]
    manifest = {
        "schema_version": "1.0",
        "record_type": "lyric_technique_pilot_batch_manifest",
        "queue_root": str(queue_root),
        "output_root": str(output_root),
        "counts": {
            "eligible_candidates": len(candidates),
            "selected": len(selected),
            "batch_size": batch_size,
            "excluded_track_ids": len(excluded),
        },
        "exclude_track_ids": sorted(excluded),
        "selected_tracks": [
            {
                "track_id": _safe_text(record.get("track_identity", {}).get("track_id")),
                "artist_id": _safe_text(record.get("track_identity", {}).get("artist_id")),
                "canonical_title": _safe_text(record.get("track_identity", {}).get("canonical_title")),
                "producer": _safe_text(record.get("metadata_context", {}).get("producer")),
                "original_platform": _safe_text(record.get("metadata_context", {}).get("original_platform")),
                "official_uploads": record.get("acquisition_sources", {}).get("official_uploads", []),
                "priority_score": _priority_score(record),
            }
            for record in selected
        ],
    }
    manifest_path = write_json(output_root / "lyric_technique_pilot_batch.json", manifest)
    manifest["manifest_path"] = str(manifest_path)
    return manifest
