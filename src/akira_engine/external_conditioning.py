from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_track_filename(artist_id: str, track_id: str) -> str:
    clean_track_id = str(track_id).strip()
    prefix = f"{artist_id}_"
    if clean_track_id.startswith(prefix):
        clean_track_id = clean_track_id[len(prefix) :]
    return f"{clean_track_id}.conditioning.json"


def active_queue_track_ids(project_root: Path, artist_id: str) -> list[str]:
    queue_path = project_root / "data" / artist_id / "reference_tracks" / "conditioning_queue.json"
    queue = load_json(queue_path)
    return [
        str(item.get("track_id", "")).strip()
        for item in queue.get("queue", [])
        if str(item.get("status", "")).strip().lower() != "pending" and str(item.get("track_id", "")).strip()
    ]


def queue_track_ids(project_root: Path, artist_id: str, queue_filename: str) -> list[str]:
    queue_path = project_root / "data" / artist_id / "reference_tracks" / queue_filename
    queue = load_json(queue_path)
    return [
        str(item.get("track_id", "")).strip()
        for item in queue.get("queue", [])
        if str(item.get("status", "")).strip().lower() != "pending" and str(item.get("track_id", "")).strip()
    ]


def build_external_handoff_payload(
    project_root: Path,
    artist_id: str,
    *,
    queue_filename: str = "conditioning_queue.json",
    required_external_work: list[str] | None = None,
) -> dict[str, Any]:
    target_dir = project_root / "data" / artist_id / "reference_tracks"
    track_ids = queue_track_ids(project_root, artist_id, queue_filename)
    work_items = required_external_work or [
        "full_lyric_grounding",
        "section_analysis_expansion",
        "source_provenance_strengthening",
        "audio_enrichment_if_available",
    ]
    tracks: list[dict[str, Any]] = []
    for track_id in track_ids:
        target_path = target_dir / canonical_track_filename(artist_id, track_id)
        current = load_json(target_path)
        tracks.append(
            {
                "track_id": track_id,
                "target_path": str(target_path),
                "full_text_status": current.get("lyric_ground_truth", {}).get("full_text_status", ""),
                "current_grade_hint": current.get("quality_control", {}).get("ready_for_prompting", False),
                "required_external_work": work_items,
            }
        )
    return {
        "schema_version": "1.0",
        "artist_id": artist_id,
        "queue_filename": queue_filename,
        "target_dir": str(target_dir),
        "track_count": len(tracks),
        "tracks": tracks,
    }


def validate_external_record(payload: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    track_id = str(payload.get("track_identity", {}).get("track_id") or payload.get("track_id") or "").strip()
    if not track_id:
        issues.append("track_id missing")
    source_provenance = payload.get("source_provenance", {})
    lyric_ground_truth = payload.get("lyric_ground_truth", {})
    section_analysis = payload.get("section_analysis", [])

    if not source_provenance.get("lyric_sources"):
        issues.append("lyric_sources missing")
    if not source_provenance.get("metadata_sources"):
        issues.append("metadata_sources missing")
    if lyric_ground_truth.get("full_text_status") != "full":
        issues.append("full_text_status is not full")
    sections = lyric_ground_truth.get("sections", [])
    if not isinstance(sections, list) or len(sections) < 5:
        issues.append("lyric_ground_truth.sections has fewer than 5 sections")
    hooks = lyric_ground_truth.get("hook_lines", [])
    if not isinstance(hooks, list) or len(hooks) < 2:
        issues.append("hook_lines has fewer than 2 items")
    if not isinstance(section_analysis, list) or len(section_analysis) < 5:
        issues.append("section_analysis has fewer than 5 entries")
    return issues
