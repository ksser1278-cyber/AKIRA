from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .training_data import write_json
from .vocaloid_metadata_intake import _fetch_artist_songs, _vocadb_get_json, _is_excluded_variant, _is_synthetic_voice_track


def _safe_text(value: Any) -> str:
    return str(value or "").strip()


def _looks_placeholder_name(name: str) -> bool:
    stripped = _safe_text(name)
    if not stripped:
        return True
    if len(stripped) <= 1:
        return True
    bad_fragments = ["unknown", "？？", "???", "___", " ️", "‎"]
    lowered = stripped.lower()
    return any(fragment in stripped or fragment in lowered for fragment in bad_fragments)


def _fetch_producer_page(*, start: int, max_entries: int) -> dict[str, Any]:
    return _vocadb_get_json(
        "/artists",
        {
            "start": start,
            "maxEntries": max_entries,
            "getTotalCount": "true",
            "artistTypes": "Producer",
            "sort": "SongCount",
            "lang": "Default",
        },
    )


def _load_existing_artist_ids(intake_root: Path) -> set[int]:
    known: set[int] = set()
    for path in intake_root.glob("vocadb_artist_seed_map*.json"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        records = payload.get("artists", []) if isinstance(payload, dict) else []
        for record in records:
            if not isinstance(record, dict):
                continue
            artist_id = record.get("vocadb_artist_id")
            if artist_id in (None, ""):
                continue
            try:
                known.add(int(artist_id))
            except Exception:
                continue
    return known


def discover_vocadb_producers(
    *,
    intake_root: Path,
    output_root: Path,
    page_count: int = 5,
    page_size: int = 50,
    sample_song_entries: int = 25,
    min_synthetic_songs: int = 3,
    max_candidates: int = 25,
) -> dict[str, Any]:
    intake_root = intake_root.resolve()
    output_root = output_root.resolve()
    output_root.mkdir(parents=True, exist_ok=True)

    known_artist_ids = _load_existing_artist_ids(intake_root)
    scanned: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []

    for page_index in range(page_count):
        start = page_index * page_size
        artist_page = _fetch_producer_page(start=start, max_entries=page_size)
        for item in artist_page.get("items", []):
            artist_id = int(item.get("id", 0) or 0)
            artist_name = _safe_text(item.get("name"))
            if not artist_id:
                continue
            if artist_id in known_artist_ids:
                scanned.append(
                    {
                        "artist_id": artist_id,
                        "artist_name": artist_name,
                        "decision": "skip_known",
                    }
                )
                continue
            if _looks_placeholder_name(artist_name):
                scanned.append(
                    {
                        "artist_id": artist_id,
                        "artist_name": artist_name,
                        "decision": "skip_placeholder_name",
                    }
                )
                continue

            songs = _fetch_artist_songs(artist_id=artist_id, max_entries=sample_song_entries).get("items", [])
            synthetic_count = 0
            for song in songs:
                if _is_excluded_variant(song):
                    continue
                if _is_synthetic_voice_track(song):
                    synthetic_count += 1

            record = {
                "artist_id": artist_id,
                "artist_name": artist_name,
                "artist_type": _safe_text(item.get("artistType")) or "Producer",
                "sampled_song_entries": len(songs),
                "synthetic_candidate_songs": synthetic_count,
                "decision": "candidate" if synthetic_count >= min_synthetic_songs else "skip_low_synthetic_support",
            }
            scanned.append(record)
            if record["decision"] == "candidate":
                candidates.append(record)

    candidates.sort(key=lambda item: (-int(item["synthetic_candidate_songs"]), item["artist_name"].lower()))
    selected_candidates = candidates[:max_candidates]
    candidate_map = {
        "schema_version": "1.0",
        "record_type": "vocadb_artist_seed_map",
        "notes": "Auto-discovered producer candidates from VocaDB producer listing with synthetic-song support sampling.",
        "artists": [
            {
                "display_name": item["artist_name"],
                "query_name": item["artist_name"],
                "vocadb_artist_id": item["artist_id"],
                "status": "candidate",
                "enabled": False,
                "notes": f"Auto-discovered. synthetic_candidate_songs={item['synthetic_candidate_songs']} over {item['sampled_song_entries']} sampled songs.",
            }
            for item in selected_candidates
        ],
    }

    report = {
        "schema_version": "1.0",
        "record_type": "vocadb_producer_discovery_report",
        "intake_root": str(intake_root),
        "output_root": str(output_root),
        "counts": {
            "known_artist_ids": len(known_artist_ids),
            "scanned_records": len(scanned),
            "candidate_records": len(candidates),
            "selected_candidates": len(selected_candidates),
        },
        "settings": {
            "page_count": page_count,
            "page_size": page_size,
            "sample_song_entries": sample_song_entries,
            "min_synthetic_songs": min_synthetic_songs,
            "max_candidates": max_candidates,
        },
        "selected_candidates": selected_candidates,
        "scanned_records": scanned,
    }

    map_path = write_json(output_root / "vocadb_artist_seed_map.discovered.json", candidate_map)
    report["candidate_map_path"] = str(map_path)
    report_path = write_json(output_root / "vocadb_producer_discovery_report.json", report)
    report["manifest_path"] = str(report_path)
    return report
