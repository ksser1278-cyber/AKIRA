from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_hard_case_registry(project_root: Path) -> dict[str, Any]:
    health = load_json(project_root / "reports" / "health" / "engine_health.json")
    artists: list[dict[str, Any]] = []
    for artist in health.get("artists", []):
        artist_id = str(artist.get("artist_id", "")).strip()
        weakest = artist.get("benchmark", {}).get("weakest_tracks", [])
        rows: list[dict[str, Any]] = []
        for item in weakest:
            track_id = str(item.get("track_id", "")).strip()
            notes = [str(note).strip() for note in item.get("notes", []) if str(note).strip()]
            if not track_id or not notes:
                continue
            rows.append(
                {
                    "track_id": track_id,
                    "score": float(item.get("score", 0.0)),
                    "issues": notes,
                    "status": "open",
                    "owner": "internal" if artist_id == "deco27" else "review_only",
                }
            )
        if rows:
            artists.append({"artist_id": artist_id, "tracks": rows})
    return {
        "schema_version": "1.0",
        "record_type": "hard_case_registry",
        "artists": artists,
    }


def sync_hard_case_registry_from_manifest(
    *,
    project_root: Path,
    manifest_path: Path,
) -> dict[str, Any]:
    registry_path = project_root / "data" / "_global" / "hard_case_registry.json"
    registry = load_json(registry_path)
    manifest = load_json(manifest_path)
    artist_id = str(manifest.get("artist_id", "")).strip()
    runs = {
        str(item.get("track_id", "")).strip(): item
        for item in manifest.get("runs", [])
        if str(item.get("track_id", "")).strip()
    }
    artists = registry.get("artists", [])
    for artist in artists:
        if str(artist.get("artist_id", "")).strip() != artist_id:
            continue
        artist["benchmark_manifest_path"] = str(manifest_path)
        artist["benchmark_average_score"] = float(manifest.get("average_score", 0.0))
        for track in artist.get("tracks", []):
            track_id = str(track.get("track_id", "")).strip()
            run = runs.get(track_id)
            if not run:
                continue
            track["score"] = float(run.get("selected_score", 0.0))
            track["current_best_score"] = float(run.get("current_best_score", 0.0))
            track["current_best_candidate_id"] = str(run.get("current_best_candidate_id", "")).strip()
            track["current_best_notes"] = [
                str(note).strip()
                for note in run.get("current_best_notes", [])
                if str(note).strip()
            ]
            track["issues"] = [
                str(note).strip()
                for note in run.get("critic_notes", [])
                if str(note).strip()
            ]
    return registry
