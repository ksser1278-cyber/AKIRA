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


def _name_key(value: str) -> str:
    normalized = re.sub(r"[\s\u3000]+", " ", value).strip()
    return normalized.casefold()


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


def _scan_lyric_files(lyrics_root: Path) -> list[Path]:
    if not lyrics_root.exists():
        raise FileNotFoundError(f"lyrics_root does not exist: {lyrics_root}")
    return sorted(path for path in lyrics_root.rglob("*.txt") if path.is_file())


def _candidate_match_keys(record: dict[str, Any]) -> list[dict[str, Any]]:
    track = record.get("track_identity", {})
    track_id = _safe_text(track.get("track_id"))
    title = _safe_text(track.get("canonical_title"))
    title_variants = _safe_list(track.get("title_variants"))
    keys: list[dict[str, Any]] = []
    if track_id:
        keys.append({"key_type": "name", "key": _name_key(track_id), "mode": "track_id", "confidence": 1.0})
    if title:
        keys.append({"key_type": "name", "key": _name_key(title), "mode": "exact_title", "confidence": 0.94})
        keys.append({"key_type": "slug", "key": _slug_key(title), "mode": "normalized_title", "confidence": 0.82})
    if track_id and title:
        title_slug = _slug_key(title)
        for combined in (f"{track_id}_{title_slug}", f"{track_id}-{title_slug}", f"{track_id} {title_slug}"):
            keys.append({"key_type": "slug", "key": _slug_key(combined), "mode": "track_id_title", "confidence": 0.97})
    for variant in title_variants:
        keys.append({"key_type": "name", "key": _name_key(variant), "mode": "exact_title_variant", "confidence": 0.9})
        keys.append({"key_type": "slug", "key": _slug_key(variant), "mode": "normalized_title_variant", "confidence": 0.78})

    deduped: dict[tuple[str, str, str], dict[str, Any]] = {}
    for item in keys:
        deduped[(item["key_type"], item["key"], item["mode"])] = item
    return list(deduped.values())


def _build_lyric_file_indexes(lyric_files: list[Path]) -> dict[str, dict[str, list[Path]]]:
    name_index: dict[str, list[Path]] = {}
    slug_index: dict[str, list[Path]] = {}
    for path in lyric_files:
        name_index.setdefault(_name_key(path.stem), []).append(path)
        slug_index.setdefault(_slug_key(path.stem), []).append(path)
    return {"name": name_index, "slug": slug_index}


def _record_identity(record: dict[str, Any]) -> dict[str, str]:
    track = record.get("track_identity", {})
    credits = record.get("credits", {})
    return {
        "track_id": _safe_text(track.get("track_id")),
        "title": _safe_text(track.get("canonical_title")),
        "artist": _safe_text(credits.get("producer")) or "unknown",
    }


def build_lyrics_match_plan(
    *,
    metadata_dir: Path,
    lyrics_root: Path,
    limit: int | None = None,
) -> dict[str, Any]:
    final_metadata_dir = metadata_dir.resolve()
    final_lyrics_root = lyrics_root.resolve()
    records = _iter_metadata_records(final_metadata_dir)
    if limit is not None:
        records = records[: max(limit, 0)]

    lyric_files = _scan_lyric_files(final_lyrics_root)
    indexes = _build_lyric_file_indexes(lyric_files)
    record_candidates: list[dict[str, Any]] = []
    path_to_track_ids: dict[str, set[str]] = {}

    for metadata_path, record in records:
        identity = _record_identity(record)
        track_id = identity["track_id"]
        candidates_by_path: dict[str, dict[str, Any]] = {}
        for key_spec in _candidate_match_keys(record):
            indexed_paths = indexes[key_spec["key_type"]].get(key_spec["key"], [])
            for lyric_path in indexed_paths:
                lyric_ref = str(lyric_path.resolve())
                candidate = {
                    "lyric_path": lyric_ref,
                    "match_mode": key_spec["mode"],
                    "confidence": key_spec["confidence"],
                }
                current = candidates_by_path.get(lyric_ref)
                if current is None or candidate["confidence"] > current["confidence"]:
                    candidates_by_path[lyric_ref] = candidate
                path_to_track_ids.setdefault(lyric_ref, set()).add(track_id)

        candidates = sorted(
            candidates_by_path.values(),
            key=lambda item: (-float(item["confidence"]), item["lyric_path"]),
        )
        record_candidates.append(
            {
                **identity,
                "metadata_record_ref": str(metadata_path.resolve()),
                "candidates": candidates,
            }
        )

    matched = 0
    ambiguous = 0
    missing = 0
    matched_paths: set[str] = set()
    records_out: list[dict[str, Any]] = []

    for item in record_candidates:
        candidates = item["candidates"]
        selected = None
        status = "missing"
        reason = "no matching lyric filename"
        if candidates:
            best_confidence = float(candidates[0]["confidence"])
            best_candidates = [candidate for candidate in candidates if float(candidate["confidence"]) == best_confidence]
            shared_best = [
                candidate
                for candidate in best_candidates
                if len(path_to_track_ids.get(candidate["lyric_path"], set())) > 1
            ]
            if len(best_candidates) == 1 and not shared_best:
                selected = best_candidates[0]
                status = "matched"
                reason = "single highest-confidence lyric file"
                matched += 1
                matched_paths.add(selected["lyric_path"])
            elif shared_best:
                status = "ambiguous"
                reason = "same lyric file matches multiple metadata records"
                ambiguous += 1
            else:
                status = "ambiguous"
                reason = "multiple equal-confidence lyric files"
                ambiguous += 1
        else:
            missing += 1

        records_out.append(
            {
                "track_id": item["track_id"],
                "title": item["title"],
                "artist": item["artist"],
                "metadata_record_ref": item["metadata_record_ref"],
                "status": status,
                "reason": reason,
                "selected_lyric_path": selected["lyric_path"] if selected else "",
                "match_mode": selected["match_mode"] if selected else "",
                "confidence": selected["confidence"] if selected else 0.0,
                "candidates": candidates,
            }
        )

    candidate_paths = {
        candidate["lyric_path"]
        for item in records_out
        for candidate in item.get("candidates", [])
    }
    all_paths = {str(path.resolve()) for path in lyric_files}
    unmatched_lyrics = sorted(all_paths - candidate_paths)
    referenced_but_not_attached = sorted(candidate_paths - matched_paths)

    return {
        "schema_version": "1.0",
        "record_type": "song_analysis_lyrics_match_plan",
        "metadata_dir": str(final_metadata_dir),
        "lyrics_root": str(final_lyrics_root),
        "counts": {
            "metadata_records": len(records),
            "lyric_files": len(lyric_files),
            "matched": matched,
            "missing": missing,
            "ambiguous": ambiguous,
            "unmatched_lyrics": len(unmatched_lyrics),
            "referenced_but_not_attached": len(referenced_but_not_attached),
        },
        "records": records_out,
        "unmatched_lyrics": unmatched_lyrics,
        "referenced_but_not_attached": referenced_but_not_attached,
    }


def build_lyrics_match_report(plan: dict[str, Any]) -> str:
    counts = plan.get("counts", {})
    lines = [
        "# Song Analysis Lyrics Match Report",
        "",
        f"- Metadata records: {counts.get('metadata_records', 0)}",
        f"- Lyric files: {counts.get('lyric_files', 0)}",
        f"- Matched: {counts.get('matched', 0)}",
        f"- Missing: {counts.get('missing', 0)}",
        f"- Ambiguous: {counts.get('ambiguous', 0)}",
        f"- Unmatched lyric files: {counts.get('unmatched_lyrics', 0)}",
        "",
        "## Records",
        "",
        "| status | track_id | title | mode | confidence | lyric |",
        "|---|---|---|---|---:|---|",
    ]
    for item in plan.get("records", []):
        lyric = item.get("selected_lyric_path") or item.get("reason", "")
        lines.append(
            "| {status} | {track_id} | {title} | {mode} | {confidence:.2f} | {lyric} |".format(
                status=item.get("status", ""),
                track_id=item.get("track_id", ""),
                title=str(item.get("title", "")).replace("|", "\\|"),
                mode=item.get("match_mode", ""),
                confidence=float(item.get("confidence", 0.0) or 0.0),
                lyric=str(lyric).replace("|", "\\|"),
            )
        )
    unmatched = plan.get("unmatched_lyrics", [])
    if unmatched:
        lines.extend(["", "## Unmatched Lyric Files", ""])
        for path in unmatched[:200]:
            lines.append(f"- {path}")
    return "\n".join(lines).rstrip() + "\n"


def write_lyrics_match_outputs(*, plan: dict[str, Any], output_root: Path) -> dict[str, Any]:
    final_output_root = output_root.resolve()
    json_path = write_json(final_output_root / "lyrics_match_report.json", plan)
    md_path = write_text(final_output_root / "lyrics_match_report.md", build_lyrics_match_report(plan))
    return {"json_path": str(json_path), "md_path": str(md_path)}


def match_song_analysis_lyrics(
    *,
    metadata_dir: Path,
    lyrics_root: Path,
    output_root: Path,
    limit: int | None = None,
) -> dict[str, Any]:
    plan = build_lyrics_match_plan(
        metadata_dir=metadata_dir,
        lyrics_root=lyrics_root,
        limit=limit,
    )
    outputs = write_lyrics_match_outputs(plan=plan, output_root=output_root)
    plan["outputs"] = outputs
    return plan


def _song_input_from_metadata(
    record: dict[str, Any],
    *,
    metadata_path: Path,
    lyric_file: Path | None,
    lyric_match: dict[str, Any] | None = None,
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
            "lyrics_match_mode": _safe_text((lyric_match or {}).get("match_mode")),
            "lyrics_match_confidence": float((lyric_match or {}).get("confidence", 0.0) or 0.0),
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

    match_by_track_id: dict[str, dict[str, Any]] = {}
    match_plan: dict[str, Any] | None = None
    if final_lyrics_root is not None:
        match_plan = build_lyrics_match_plan(
            metadata_dir=final_metadata_dir,
            lyrics_root=final_lyrics_root,
            limit=limit,
        )
        write_lyrics_match_outputs(plan=match_plan, output_root=final_output_root)
        for item in match_plan.get("records", []):
            match_by_track_id[_safe_text(item.get("track_id"))] = item

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

        lyric_match = match_by_track_id.get(track_id)
        lyric_file = (
            Path(lyric_match["selected_lyric_path"])
            if lyric_match and lyric_match.get("status") == "matched" and lyric_match.get("selected_lyric_path")
            else None
        )
        song_input = _song_input_from_metadata(
            record,
            metadata_path=metadata_path,
            lyric_file=lyric_file,
            lyric_match=lyric_match,
        )
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
                "lyric_match_status": _safe_text((lyric_match or {}).get("status")) if final_lyrics_root else "",
                "lyric_match_mode": _safe_text((lyric_match or {}).get("match_mode")),
                "lyric_match_confidence": float((lyric_match or {}).get("confidence", 0.0) or 0.0),
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
        "lyrics_match_counts": (match_plan or {}).get("counts", {}),
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
