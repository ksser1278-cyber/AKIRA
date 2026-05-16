from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from ..vocaloid_metadata_intake import seed_vocadb_bulk_metadata_intake
from .loader import write_json, write_text


DEFAULT_ANALYSIS_GOALS = [
    "songwriting_intent",
    "composition_intent",
    "hook_design",
    "ai_reconstruction",
]


def _safe_text(value: Any) -> str:
    return str(value or "").strip()


def _safe_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [_safe_text(item) for item in value if _safe_text(item)]
    text = _safe_text(value)
    return [text] if text else []


def _slug_key(value: str) -> str:
    lowered = value.lower()
    normalized = re.sub(r"[\s\u3000]+", "_", lowered)
    normalized = re.sub(r"[^\w\-]+", "", normalized, flags=re.UNICODE)
    return normalized.strip("_") or "untitled"


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return payload if isinstance(payload, dict) else None


def _iter_metadata_records(metadata_dir: Path) -> list[tuple[Path, dict[str, Any]]]:
    records: list[tuple[Path, dict[str, Any]]] = []
    for path in sorted(metadata_dir.glob("*.json")):
        payload = _read_json(path)
        if not payload:
            continue
        if payload.get("record_type") != "vocaloid_metadata_record":
            continue
        records.append((path, payload))
    return records


def _source_urls(metadata_sources: Any, *, source_type: str | None = None) -> list[str]:
    urls: list[str] = []
    iterable = metadata_sources if isinstance(metadata_sources, list) else []
    for source in iterable:
        if not isinstance(source, dict):
            continue
        if source_type and _safe_text(source.get("source_type")) != source_type:
            continue
        url = _safe_text(source.get("url"))
        if url:
            urls.append(url)
    return urls


def _choose_primary_url(record: dict[str, Any]) -> str:
    sources = record.get("metadata_sources", [])
    official = _source_urls(sources, source_type="official_upload")
    if official:
        return official[0]
    vocadb = _source_urls(sources, source_type="vocadb")
    if vocadb:
        return vocadb[0]
    any_url = _source_urls(sources)
    return any_url[0] if any_url else ""


def _find_vocadb_url(record: dict[str, Any]) -> str:
    urls = _source_urls(record.get("metadata_sources", []), source_type="vocadb")
    return urls[0] if urls else ""


def _find_local_lyrics(record: dict[str, Any], lyrics_root: Path | None) -> Path | None:
    if lyrics_root is None:
        return None
    track = record.get("track_identity", {})
    track_id = _safe_text(track.get("track_id"))
    title = _safe_text(track.get("canonical_title"))
    candidate_names = []
    if track_id:
        candidate_names.append(f"{track_id}.txt")
    if title:
        candidate_names.append(f"{title}.txt")
        candidate_names.append(f"{_slug_key(title)}.txt")
    for name in dict.fromkeys(candidate_names):
        candidate = lyrics_root / name
        if candidate.exists() and candidate.is_file():
            return candidate
    return None


def _song_input_from_metadata(
    record: dict[str, Any],
    *,
    metadata_path: Path,
    lyric_file: Path | None,
) -> dict[str, Any]:
    track = record.get("track_identity", {})
    credits = record.get("credits", {})
    vocal_synthesis = record.get("vocal_synthesis", {})
    release = record.get("release_context", {})
    voicebanks = _safe_list(vocal_synthesis.get("voicebanks"))
    primary_url = _choose_primary_url(record)
    official_urls = _source_urls(record.get("metadata_sources", []), source_type="official_upload")
    return {
        "song_id": _safe_text(track.get("track_id")),
        "title": _safe_text(track.get("canonical_title")),
        "artist": _safe_text(credits.get("producer")) or "unknown",
        "vocal": " / ".join(voicebanks),
        "url": primary_url,
        "language": "ja",
        "analysis_goal": DEFAULT_ANALYSIS_GOALS,
        "known_metadata": {
            "lyricist": _safe_text(credits.get("lyricist")),
            "composer": _safe_text(credits.get("composer")),
            "arranger": _safe_text(credits.get("arranger")),
            "producer": _safe_text(credits.get("producer")),
            "release_date": _safe_text(release.get("original_upload_date")),
            "genre": "",
            "engine_family": _safe_text(vocal_synthesis.get("engine_family")),
            "voicebanks": voicebanks,
            "original_platform": _safe_text(release.get("original_platform")),
            "vocadb_url": _find_vocadb_url(record),
        },
        "available_sources": {
            "lyrics": lyric_file is not None,
            "audio": False,
            "mv": bool(official_urls),
            "official_commentary": False,
            "instrumental": False,
        },
        "collection": {
            "metadata_record_ref": str(metadata_path.resolve()),
            "lyrics_status": "local_user_supplied" if lyric_file else "missing_user_supplied",
            "lyrics_ref": str(lyric_file.resolve()) if lyric_file else "",
            "rights_status": "metadata_only_not_lyric_training_clearance",
            "notes": (
                "Lyrics are attached only when a local lyrics_root file matches the track. "
                "Web metadata does not grant lyric-training rights."
            ),
        },
    }


def _empty_audio_features() -> dict[str, Any]:
    return {
        "bpm": None,
        "key": "",
        "chord_notes": "",
        "section_markers": [],
        "source_status": "not_collected",
    }


def materialize_song_analysis_inputs_from_metadata(
    *,
    metadata_dir: Path,
    output_root: Path,
    lyrics_root: Path | None = None,
    limit: int | None = None,
    overwrite: bool = False,
) -> dict[str, Any]:
    final_metadata_dir = metadata_dir.resolve()
    final_output_root = output_root.resolve()
    final_lyrics_root = lyrics_root.resolve() if lyrics_root else None
    final_output_root.mkdir(parents=True, exist_ok=True)

    records = _iter_metadata_records(final_metadata_dir)
    if limit is not None:
        records = records[: max(limit, 0)]

    materialized: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    ready_for_analysis = 0

    for metadata_path, record in records:
        track = record.get("track_identity", {})
        track_id = _safe_text(track.get("track_id"))
        title = _safe_text(track.get("canonical_title"))
        if not track_id:
            skipped.append({"metadata_path": str(metadata_path), "reason": "missing_track_id"})
            continue

        package_dir = final_output_root / track_id
        song_input_path = package_dir / "song_input.json"
        if song_input_path.exists() and not overwrite:
            skipped.append({"track_id": track_id, "title": title, "reason": "package_exists"})
            continue

        lyric_file = _find_local_lyrics(record, final_lyrics_root)
        song_input = _song_input_from_metadata(record, metadata_path=metadata_path, lyric_file=lyric_file)
        write_json(song_input_path, song_input)
        write_json(package_dir / "audio_features.json", _empty_audio_features())
        write_json(
            package_dir / "source_manifest.json",
            {
                "schema_version": "1.0",
                "record_type": "song_analysis_source_manifest",
                "track_id": track_id,
                "title": title,
                "metadata_record_ref": str(metadata_path.resolve()),
                "vocadb_url": _find_vocadb_url(record),
                "primary_url": _choose_primary_url(record),
                "lyric_file_ref": str(lyric_file.resolve()) if lyric_file else "",
                "ready_for_analysis": lyric_file is not None,
            },
        )
        if lyric_file:
            write_text(package_dir / "lyrics.txt", lyric_file.read_text(encoding="utf-8"))
            ready_for_analysis += 1
        else:
            write_text(
                package_dir / "lyrics.todo.txt",
                "\n".join(
                    [
                        "Add a locally obtained lyrics.txt here before running song-analysis.",
                        "Do not treat scraped metadata as lyric-training clearance.",
                        f"track_id: {track_id}",
                        f"title: {title}",
                    ]
                ),
            )

        materialized.append(
            {
                "track_id": track_id,
                "title": title,
                "package_dir": str(package_dir),
                "ready_for_analysis": lyric_file is not None,
            }
        )

    manifest = {
        "schema_version": "1.0",
        "record_type": "song_analysis_acquisition_manifest",
        "metadata_dir": str(final_metadata_dir),
        "output_root": str(final_output_root),
        "lyrics_root": str(final_lyrics_root) if final_lyrics_root else "",
        "counts": {
            "metadata_records_seen": len(records),
            "materialized": len(materialized),
            "ready_for_analysis": ready_for_analysis,
            "skipped": len(skipped),
        },
        "materialized": materialized,
        "skipped": skipped,
    }
    manifest_path = write_json(final_output_root / "song_analysis_acquisition_manifest.json", manifest)
    manifest["manifest_path"] = str(manifest_path)
    return manifest


def scrape_vocadb_song_analysis_inputs(
    *,
    project_root: Path,
    output_root: Path,
    metadata_output_dir: Path,
    page_count: int = 1,
    page_size: int = 50,
    start_offset: int = 0,
    sort: str = "PublishDate",
    materialize_limit: int | None = None,
    lyrics_root: Path | None = None,
    overwrite: bool = False,
) -> dict[str, Any]:
    metadata_manifest = seed_vocadb_bulk_metadata_intake(
        project_root=project_root.resolve(),
        output_dir=metadata_output_dir.resolve(),
        page_count=page_count,
        page_size=page_size,
        start_offset=start_offset,
        sort=sort,
    )
    acquisition_manifest = materialize_song_analysis_inputs_from_metadata(
        metadata_dir=metadata_output_dir,
        output_root=output_root,
        lyrics_root=lyrics_root,
        limit=materialize_limit,
        overwrite=overwrite,
    )
    manifest = {
        "schema_version": "1.0",
        "record_type": "song_analysis_vocadb_scrape_manifest",
        "metadata_manifest": metadata_manifest,
        "acquisition_manifest": acquisition_manifest,
        "counts": {
            "metadata_written": metadata_manifest.get("counts", {}).get("written_records", 0),
            "materialized": acquisition_manifest.get("counts", {}).get("materialized", 0),
            "ready_for_analysis": acquisition_manifest.get("counts", {}).get("ready_for_analysis", 0),
        },
    }
    manifest_path = write_json(output_root.resolve() / "vocadb_scrape_manifest.json", manifest)
    manifest["manifest_path"] = str(manifest_path)
    return manifest
