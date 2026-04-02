from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .ingest import write_manifest


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def approved_benchmark_manifest(project_root: Path, artist_id: str) -> Path | None:
    registry_path = project_root / "data" / "benchmark_registry.json"
    if not registry_path.exists():
        return None
    registry = load_json(registry_path)
    for artist_block in registry.get("artists", []):
        if str(artist_block.get("artist_id", "")).strip() != artist_id:
            continue
        approved = str(artist_block.get("approved_manifest_path", "")).strip()
        if not approved:
            return None
        approved_path = Path(approved)
        return approved_path if approved_path.exists() else None
    return None


def latest_benchmark_manifest(project_root: Path, artist_id: str) -> Path | None:
    approved = approved_benchmark_manifest(project_root, artist_id)
    if approved is not None:
        return approved

    outputs_root = project_root / "outputs"
    patterns = [
        f"songwriter_v2_anchor_matrix*\\{artist_id}\\anchor_matrix_manifest.json",
        f"songwriter_v2_anchor_matrix*\\{artist_id}\\benchmark_manifest.json",
        f"_archive\\songwriter_v2_anchor_matrix\\*\\anchor_matrix_manifest.json",
        f"_archive\\songwriter_v2_anchor_matrix\\*\\benchmark_manifest.json",
    ]
    candidates: list[Path] = []
    for pattern in patterns:
        for path in outputs_root.glob(pattern):
            lowered = str(path).lower()
            if artist_id.lower() in lowered:
                candidates.append(path)

    def sort_key(path: Path) -> tuple[int, int, float]:
        lowered = str(path).lower()
        live_priority = 1 if "\\outputs\\_archive\\" not in lowered else 0
        version = 0
        for part in path.parts:
            matches = re.findall(r"_v(\d+)", part.lower())
            if matches:
                version = max(version, max(int(match) for match in matches))
        return (live_priority, version, path.stat().st_mtime)

    candidates.sort(key=sort_key, reverse=True)
    return candidates[0] if candidates else None


def merge_lyric_manifests(
    primary_manifest_path: Path,
    secondary_manifest_path: Path,
    output_path: Path,
) -> Path:
    primary = load_json(primary_manifest_path)
    secondary = load_json(secondary_manifest_path)

    merged_tracks = list(primary["tracks"])
    seen_track_ids = {track["track_id"] for track in merged_tracks}
    seen_lyric_paths = {track["lyric_path"] for track in merged_tracks}
    seen_source_urls = {track.get("source_url", "") for track in merged_tracks if track.get("source_url")}

    for track in secondary["tracks"]:
        if track["track_id"] in seen_track_ids:
            continue
        if track["lyric_path"] in seen_lyric_paths:
            continue
        if track.get("source_url") and track["source_url"] in seen_source_urls:
            continue

        merged_tracks.append(track)
        seen_track_ids.add(track["track_id"])
        seen_lyric_paths.add(track["lyric_path"])
        if track.get("source_url"):
            seen_source_urls.add(track["source_url"])

    merged_manifest = {
        **primary,
        "collection_method": (
            f"{primary['collection_method']} + merged with {secondary_manifest_path.name}"
        ),
        "tracks": merged_tracks,
    }
    write_manifest(output_path, merged_manifest)
    return output_path
