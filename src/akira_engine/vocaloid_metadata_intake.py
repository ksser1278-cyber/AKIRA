from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from .training_data import write_json


VOCADB_API_ROOT = "https://vocadb.net/api"
VOCADB_USER_AGENT = "AKIRA-ENGINE/1.0 vocaloid-metadata-intake"
SYNTHETIC_ARTIST_TYPE_HINTS = {
    "vocaloid",
    "utau",
    "cevio",
    "synthesizerv",
    "synthesizer v",
    "voice synthesizer",
    "other voice synthesizer",
}
EXCLUDED_SONG_TYPE_HINTS = {
    "remix",
    "cover",
    "instrumental",
    "medley",
    "musicpv",
    "drama",
}
EXCLUDED_TITLE_HINTS = {
    "remix",
    "cover",
    "inst.",
    "instrumental",
    "medley",
    "short ver.",
}


def _safe_text(value: Any) -> str:
    return str(value or "").strip()


def load_artist_list(path: Path) -> list[str]:
    if not path.exists():
        return []
    artists: list[str] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        artists.append(line)
    return artists


def load_artist_seed_map(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        records = payload.get("artists", [])
    elif isinstance(payload, list):
        records = payload
    else:
        return []
    return [record for record in records if isinstance(record, dict)]


def _vocadb_get_json(path: str, params: dict[str, Any]) -> dict[str, Any]:
    query = urllib.parse.urlencode({key: value for key, value in params.items() if value is not None})
    url = f"{VOCADB_API_ROOT}{path}?{query}" if query else f"{VOCADB_API_ROOT}{path}"
    request = urllib.request.Request(url, headers={"User-Agent": VOCADB_USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def _fetch_song_search(*, query: str, max_entries: int) -> dict[str, Any]:
    return _vocadb_get_json(
        "/songs",
        {
            "query": query,
            "maxEntries": max_entries,
            "getTotalCount": "true",
            "fields": "Artists,AdditionalNames,PVs,Tags",
            "lang": "Default",
            "nameMatchMode": "Auto",
        },
    )


def _fetch_artist_search(*, query: str, max_entries: int = 10) -> dict[str, Any]:
    return _vocadb_get_json(
        "/artists",
        {
            "query": query,
            "maxEntries": max_entries,
            "getTotalCount": "true",
            "fields": "Names",
            "lang": "Default",
            "nameMatchMode": "Auto",
        },
    )


def _fetch_artist_songs(*, artist_id: int, max_entries: int) -> dict[str, Any]:
    return _vocadb_get_json(
        "/songs",
        {
            "artistId[]": artist_id,
            "maxEntries": max_entries,
            "getTotalCount": "true",
            "fields": "Artists,AdditionalNames,PVs,Tags",
            "lang": "Default",
        },
    )


def _fetch_song_catalog_page(*, start: int, max_entries: int, sort: str = "PublishDate") -> dict[str, Any]:
    return _vocadb_get_json(
        "/songs",
        {
            "start": start,
            "maxEntries": max_entries,
            "getTotalCount": "true",
            "fields": "Artists,AdditionalNames,PVs,Tags",
            "lang": "Default",
            "sort": sort,
        },
    )


def _artist_type_tokens(item: dict[str, Any]) -> list[str]:
    tokens: list[str] = []
    for artist_entry in item.get("artists", []):
        artist = artist_entry.get("artist", {})
        artist_type = _safe_text(artist.get("artistType"))
        if artist_type:
            tokens.append(artist_type.lower())
    return tokens


def _is_synthetic_voice_track(item: dict[str, Any]) -> bool:
    tokens = _artist_type_tokens(item)
    return any(any(hint in token for hint in SYNTHETIC_ARTIST_TYPE_HINTS) for token in tokens)


def _is_excluded_variant(item: dict[str, Any]) -> bool:
    song_type = _safe_text(item.get("songType")).lower()
    if song_type in EXCLUDED_SONG_TYPE_HINTS:
        return True
    title_blob = " ".join(
        [
            _safe_text(item.get("defaultName")).lower(),
            _safe_text(item.get("name")).lower(),
            _safe_text(item.get("additionalNames")).lower(),
        ]
    )
    return any(hint in title_blob for hint in EXCLUDED_TITLE_HINTS)


def _voicebanks(item: dict[str, Any]) -> list[str]:
    names: list[str] = []
    for artist_entry in item.get("artists", []):
        artist = artist_entry.get("artist", {})
        if "vocalist" not in _safe_text(artist_entry.get("categories")).lower():
            continue
        name = _safe_text(artist.get("name")) or _safe_text(artist_entry.get("name"))
        if name:
            names.append(name)
    return names


def _producers(item: dict[str, Any]) -> list[str]:
    names: list[str] = []
    for artist_entry in item.get("artists", []):
        categories = _safe_text(artist_entry.get("categories")).lower()
        if "producer" not in categories and "composer" not in categories and "band" not in categories:
            continue
        artist = artist_entry.get("artist", {})
        name = _safe_text(artist.get("name")) or _safe_text(artist_entry.get("name"))
        if name:
            names.append(name)
    return names


def _engine_family(item: dict[str, Any]) -> str:
    artist_types = _artist_type_tokens(item)
    joined = " ".join(artist_types)
    if "vocaloid" in joined:
        return "vocaloid"
    if "synthesizer v" in joined or "synthesizerv" in joined:
        return "synthesizer_v"
    if "cevio" in joined:
        return "cevio"
    if "utau" in joined:
        return "utau"
    if "voiceroid" in joined:
        return "voiceroid_song_culture"
    return "unknown"


def _original_platform(item: dict[str, Any]) -> str:
    pvs = item.get("pvs", [])
    for pv in pvs:
        if _safe_text(pv.get("pvType")).lower() == "original":
            service = _safe_text(pv.get("service")).lower()
            if service == "youtube":
                return "youtube"
            if service == "niconicomylist" or service == "niconico":
                return "niconico"
            if service == "bilibili":
                return "bilibili"
            return "other"
    return "unknown"


def _original_upload_url(item: dict[str, Any]) -> str:
    for pv in item.get("pvs", []):
        if _safe_text(pv.get("pvType")).lower() == "original":
            return _safe_text(pv.get("url"))
    return ""


def _record_from_vocadb_item(*, item: dict[str, Any], seed_context: str) -> dict[str, Any]:
    song_id = int(item.get("id"))
    title = _safe_text(item.get("defaultName")) or _safe_text(item.get("name")) or f"vocadb_song_{song_id}"
    track_id = f"vocadb_{song_id}"
    producers = _producers(item)
    voicebanks = _voicebanks(item)
    upload_url = _original_upload_url(item)
    metadata_sources = [
        {
            "label": f"VocaDB song {song_id}",
            "source_type": "vocadb",
            "url": f"https://vocadb.net/S/{song_id}",
            "notes": f"Seeded from VocaDB context: {seed_context}",
        }
    ]
    if upload_url:
        metadata_sources.append(
            {
                "label": "Original upload",
                "source_type": "official_upload",
                "url": upload_url,
                "notes": "Original PV reference from VocaDB entry.",
            }
        )
    return {
        "schema_version": "1.0",
        "record_type": "vocaloid_metadata_record",
        "track_identity": {
            "track_id": track_id,
            "canonical_title": title,
            "title_variants": [name for name in {_safe_text(item.get("name")), _safe_text(item.get("additionalNames"))} if name and name != title],
        },
        "canonical_basis": {
            "is_vocaloid_canonical": True,
            "inclusion_basis": "vocadb_canonical",
            "notes": f"Seeded from VocaDB context '{seed_context}' and filtered to synthetic-voice track candidates.",
        },
        "vocal_synthesis": {
            "engine_family": _engine_family(item),
            "voicebanks": voicebanks or ["unknown"],
            "notes": "",
        },
        "credits": {
            "producer": " / ".join(producers) if producers else "unknown",
            "lyricist": "",
            "composer": "",
            "arranger": "",
            "featured_creators": [],
        },
        "release_context": {
            "original_platform": _original_platform(item),
            "original_upload_date": _safe_text(item.get("publishDate")),
            "album_or_tie_in": "",
            "variant_relations": [],
        },
        "metadata_sources": metadata_sources,
        "collection_status": {
            "metadata_quality": "seed",
            "canonical_review_status": "needs_review",
            "notes": "Auto-seeded from VocaDB search results. Review canonical basis and producer normalization.",
        },
    }


def seed_vocadb_metadata_intake(
    *,
    project_root: Path,
    queries: list[str] | None,
    artist_ids: list[int] | None,
    artist_names: list[str] | None,
    artist_map: list[dict[str, Any]] | None,
    output_dir: Path,
    max_entries: int = 50,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    written_records: list[dict[str, Any]] = []
    skipped_items: list[dict[str, Any]] = []
    seen_track_ids: set[str] = set()
    seed_inputs: list[tuple[str, dict[str, Any]]] = []

    for query in queries or []:
        seed_inputs.append((f"query:{query}", _fetch_song_search(query=query, max_entries=max_entries)))

    resolved_artist_ids: list[dict[str, Any]] = []
    skipped_artist_map_entries: list[dict[str, Any]] = []
    for artist_entry in artist_map or []:
        display_name = _safe_text(artist_entry.get("display_name")) or _safe_text(artist_entry.get("artist_name"))
        artist_id = artist_entry.get("vocadb_artist_id")
        status = _safe_text(artist_entry.get("status")).lower() or "confirmed"
        enabled = artist_entry.get("enabled", True) is not False
        if not enabled:
            skipped_artist_map_entries.append({"display_name": display_name, "reason": "disabled"})
            continue
        if status != "confirmed":
            skipped_artist_map_entries.append(
                {"display_name": display_name, "reason": f"status:{status or 'unresolved'}"}
            )
            continue
        if artist_id in (None, ""):
            skipped_artist_map_entries.append({"display_name": display_name, "reason": "missing_vocadb_artist_id"})
            continue
        resolved_artist_ids.append(
            {
                "artist_id": int(artist_id),
                "artist_name": display_name,
                "resolved_from": _safe_text(artist_entry.get("query_name")) or display_name or str(artist_id),
                "resolution_source": "artist_map",
            }
        )

    for artist_name in artist_names or []:
        artist_response = _fetch_artist_search(query=artist_name)
        for artist_item in artist_response.get("items", [])[:1]:
            resolved_artist_ids.append(
                {
                    "artist_id": int(artist_item.get("id")),
                    "artist_name": _safe_text(artist_item.get("name")) or artist_name,
                    "resolved_from": artist_name,
                    "resolution_source": "artist_search",
                }
            )

    for artist_id in artist_ids or []:
        resolved_artist_ids.append(
            {
                "artist_id": int(artist_id),
                "artist_name": "",
                "resolved_from": str(artist_id),
                "resolution_source": "artist_id",
            }
        )

    for artist_info in resolved_artist_ids:
        artist_id = int(artist_info["artist_id"])
        artist_name = _safe_text(artist_info.get("artist_name")) or f"artist_{artist_id}"
        seed_inputs.append(
            (
                f"artist:{artist_id}:{artist_name}",
                _fetch_artist_songs(artist_id=artist_id, max_entries=max_entries),
            )
        )

    for seed_context, response in seed_inputs:
        for item in response.get("items", []):
            song_id = int(item.get("id", 0) or 0)
            if not song_id:
                skipped_items.append({"seed_context": seed_context, "reason": "missing_song_id"})
                continue
            if _is_excluded_variant(item):
                skipped_items.append({"seed_context": seed_context, "song_id": song_id, "reason": "excluded_variant"})
                continue
            if not _is_synthetic_voice_track(item):
                skipped_items.append({"seed_context": seed_context, "song_id": song_id, "reason": "non_synthetic_voice_candidate"})
                continue
            record = _record_from_vocadb_item(item=item, seed_context=seed_context)
            track_id = record["track_identity"]["track_id"]
            if track_id in seen_track_ids:
                continue
            seen_track_ids.add(track_id)
            output_path = output_dir / f"{record['track_identity']['track_id']}.json"
            write_json(output_path, record)
            written_records.append(
                {
                    "seed_context": seed_context,
                    "track_id": record["track_identity"]["track_id"],
                    "title": record["track_identity"]["canonical_title"],
                    "path": str(output_path),
                }
            )

    manifest = {
        "schema_version": "1.0",
        "record_type": "vocaloid_metadata_seed_manifest",
        "project_root": str(project_root.resolve()),
        "output_dir": str(output_dir.resolve()),
        "queries": queries or [],
        "artist_ids": artist_ids or [],
        "artist_names": artist_names or [],
        "artist_map_entries": artist_map or [],
        "resolved_artist_ids": resolved_artist_ids,
        "skipped_artist_map_entries": skipped_artist_map_entries,
        "counts": {
            "written_records": len(written_records),
            "skipped_items": len(skipped_items),
            "resolved_artist_ids_count": len(resolved_artist_ids),
            "skipped_artist_map_entries": len(skipped_artist_map_entries),
        },
        "written_records": written_records,
        "skipped_items": skipped_items,
    }
    manifest_path = write_json(output_dir / "vocadb_seed_manifest.json", manifest)
    manifest["manifest_path"] = str(manifest_path)
    return manifest


def seed_vocadb_bulk_metadata_intake(
    *,
    project_root: Path,
    output_dir: Path,
    page_count: int = 10,
    page_size: int = 50,
    start_offset: int = 0,
    sort: str = "PublishDate",
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    written_records: list[dict[str, Any]] = []
    skipped_items: list[dict[str, Any]] = []
    seen_track_ids: set[str] = set()
    pages_scanned: list[dict[str, Any]] = []

    for page_index in range(page_count):
        start = start_offset + page_index * page_size
        response = _fetch_song_catalog_page(start=start, max_entries=page_size, sort=sort)
        pages_scanned.append(
            {
                "page_index": page_index,
                "start": start,
                "returned_items": len(response.get("items", [])),
                "total_count": int(response.get("totalCount", 0) or 0),
            }
        )
        for item in response.get("items", []):
            song_id = int(item.get("id", 0) or 0)
            if not song_id:
                skipped_items.append({"seed_context": f"bulk:{start}", "reason": "missing_song_id"})
                continue
            if _is_excluded_variant(item):
                skipped_items.append({"seed_context": f"bulk:{start}", "song_id": song_id, "reason": "excluded_variant"})
                continue
            if not _is_synthetic_voice_track(item):
                skipped_items.append({"seed_context": f"bulk:{start}", "song_id": song_id, "reason": "non_synthetic_voice_candidate"})
                continue
            record = _record_from_vocadb_item(item=item, seed_context=f"bulk_catalog:start={start}:sort={sort}")
            track_id = record["track_identity"]["track_id"]
            if track_id in seen_track_ids:
                continue
            seen_track_ids.add(track_id)
            output_path = output_dir / f"{track_id}.json"
            write_json(output_path, record)
            written_records.append(
                {
                    "seed_context": f"bulk:{start}",
                    "track_id": track_id,
                    "title": record["track_identity"]["canonical_title"],
                    "path": str(output_path),
                }
            )

    manifest = {
        "schema_version": "1.0",
        "record_type": "vocaloid_metadata_bulk_seed_manifest",
        "project_root": str(project_root.resolve()),
        "output_dir": str(output_dir.resolve()),
        "page_count": page_count,
        "page_size": page_size,
        "start_offset": start_offset,
        "sort": sort,
        "pages_scanned": pages_scanned,
        "counts": {
            "written_records": len(written_records),
            "skipped_items": len(skipped_items),
            "pages_scanned": len(pages_scanned),
        },
        "written_records": written_records,
        "skipped_items": skipped_items,
    }
    manifest_path = write_json(output_dir / "vocadb_bulk_seed_manifest.json", manifest)
    manifest["manifest_path"] = str(manifest_path)
    return manifest
