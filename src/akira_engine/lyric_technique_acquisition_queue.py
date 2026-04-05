from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .training_data import write_json, write_jsonl


def _safe_text(value: Any) -> str:
    return str(value or "").strip()


def _slugify(text: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", text.lower())
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    return normalized


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _has_broken_text(value: str) -> bool:
    if ("\ufffd" in value) or ("??" in value):
        return True
    if re.search(r"[\uac00-\ud7af]", value):
        return True
    if re.search(r"[\u0080-\u009f]", value):
        return True
    return False


def _contains_japanese_text(value: str) -> bool:
    return bool(re.search(r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff]", value))


def _language_hint(payload: dict[str, Any]) -> str:
    track = payload.get("track_identity", {})
    candidates = [_safe_text(track.get("canonical_title"))]
    candidates.extend(_safe_text(item) for item in track.get("title_variants", []))
    candidates = [item for item in candidates if item]
    if any(_contains_japanese_text(item) for item in candidates):
        return "ja_or_mixed"
    if any(re.search(r"[A-Za-z]", item) for item in candidates):
        return "non_ja_likely"
    return "unknown"


def _resolve_artist_id(payload: dict[str, Any]) -> str:
    producer = _safe_text(payload.get("credits", {}).get("producer"))
    if producer:
        return _slugify(producer) or "unknown_artist"
    return "unknown_artist"


def _source_urls(payload: dict[str, Any], source_type: str) -> list[str]:
    urls: list[str] = []
    for source in payload.get("metadata_sources", []):
        if _safe_text(source.get("source_type")) == source_type:
            url = _safe_text(source.get("url"))
            if url:
                urls.append(url)
    return urls


def _queue_flags(payload: dict[str, Any]) -> list[str]:
    flags: list[str] = []
    title = _safe_text(payload.get("track_identity", {}).get("canonical_title"))
    if not title:
        flags.append("track_identity:missing_title")
    elif _has_broken_text(title):
        flags.append("track_identity:corrupted_title")

    voicebanks = payload.get("vocal_synthesis", {}).get("voicebanks", [])
    if not voicebanks:
        flags.append("vocal_synthesis:missing_voicebank")
    elif any(_has_broken_text(_safe_text(item)) for item in voicebanks):
        flags.append("vocal_synthesis:corrupted_voicebank")

    if not _source_urls(payload, "official_upload"):
        flags.append("source:missing_official_upload")
    if not _source_urls(payload, "vocadb"):
        flags.append("source:missing_vocadb_page")

    platform = _safe_text(payload.get("release_context", {}).get("original_platform"))
    if not platform or platform == "unknown":
        flags.append("release_context:unknown_platform")
    if _language_hint(payload) != "ja_or_mixed":
        flags.append("language:non_japanese_or_unknown_title_space")
    return flags


def _priority(payload: dict[str, Any], flags: list[str]) -> str:
    if any(flag.startswith("source:missing_official_upload") for flag in flags):
        return "patch_first"
    if any(
        flag.startswith(prefix)
        for flag in flags
        for prefix in [
            "vocal_synthesis:corrupted_voicebank",
            "track_identity:corrupted_title",
            "language:non_japanese_or_unknown_title_space",
        ]
    ):
        return "review_first"
    return "ready_for_lyric_acquisition"


def _build_queue_record(payload: dict[str, Any]) -> dict[str, Any]:
    track_id = _safe_text(payload.get("track_identity", {}).get("track_id"))
    title = _safe_text(payload.get("track_identity", {}).get("canonical_title"))
    artist_id = _resolve_artist_id(payload)
    producer = _safe_text(payload.get("credits", {}).get("producer"))
    engine_family = _safe_text(payload.get("vocal_synthesis", {}).get("engine_family")) or "unknown"
    voicebanks = [_safe_text(item) for item in payload.get("vocal_synthesis", {}).get("voicebanks", []) if _safe_text(item)]
    flags = _queue_flags(payload)
    return {
        "schema_version": "1.0",
        "record_type": "lyric_technique_acquisition_record",
        "track_identity": {
            "track_id": track_id,
            "artist_id": artist_id,
            "canonical_title": title,
        },
        "metadata_context": {
            "producer": producer,
            "engine_family": engine_family,
            "voicebanks": voicebanks,
            "original_platform": _safe_text(payload.get("release_context", {}).get("original_platform")),
            "original_upload_date": _safe_text(payload.get("release_context", {}).get("original_upload_date")),
            "title_variants": [
                _safe_text(item)
                for item in payload.get("track_identity", {}).get("title_variants", [])
                if _safe_text(item)
            ],
            "language_hint": _language_hint(payload),
        },
        "acquisition_sources": {
            "vocadb_pages": _source_urls(payload, "vocadb"),
            "official_uploads": _source_urls(payload, "official_upload"),
            "other_metadata_sources": [
                {
                    "label": _safe_text(source.get("label")),
                    "source_type": _safe_text(source.get("source_type")),
                    "url": _safe_text(source.get("url")),
                }
                for source in payload.get("metadata_sources", [])
                if _safe_text(source.get("source_type")) not in {"vocadb", "official_upload"}
            ],
        },
        "queue_status": {
            "priority": _priority(payload, flags),
            "ready_for_lyric_grounding": not any(
                flag.startswith(prefix)
                for flag in flags
                for prefix in [
                    "source:missing_official_upload",
                    "track_identity:corrupted_title",
                    "vocal_synthesis:corrupted_voicebank",
                    "language:non_japanese_or_unknown_title_space",
                ]
            ),
            "blocking_flags": flags,
            "next_step": (
                "Acquire grounded lyric source and section map in vocadb track-id space."
                if not any(
                    flag.startswith(prefix)
                    for flag in flags
                    for prefix in [
                        "source:missing_official_upload",
                        "track_identity:corrupted_title",
                        "vocal_synthesis:corrupted_voicebank",
                        "language:non_japanese_or_unknown_title_space",
                    ]
                )
                else "Patch metadata quality or exclude non-Japanese title-space tracks before lyric acquisition."
            ),
        },
    }


def build_lyric_technique_acquisition_queue(
    *,
    corpus_root: Path,
    output_root: Path,
) -> dict[str, Any]:
    corpus_root = corpus_root.resolve()
    output_root = output_root.resolve()
    accepted_dir = corpus_root / "accepted"
    records_dir = output_root / "records"
    records_dir.mkdir(parents=True, exist_ok=True)

    records: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    for path in sorted(accepted_dir.glob("vocadb_*.json")):
        try:
            payload = _load_json(path)
        except Exception as exc:
            skipped.append({"path": str(path), "reason": f"invalid_json:{type(exc).__name__}"})
            continue
        track_id = _safe_text(payload.get("track_identity", {}).get("track_id"))
        if not track_id:
            skipped.append({"path": str(path), "reason": "missing_track_id"})
            continue
        record = _build_queue_record(payload)
        records.append(record)
        write_json(records_dir / f"{track_id}.json", record)

    jsonl_path = write_jsonl(output_root / "lyric_technique_acquisition_queue.jsonl", records)
    ready_count = sum(1 for record in records if record["queue_status"]["ready_for_lyric_grounding"])
    manifest = {
        "schema_version": "1.0",
        "record_type": "lyric_technique_acquisition_manifest",
        "corpus_root": str(corpus_root),
        "output_root": str(output_root),
        "counts": {
            "records": len(records),
            "ready_for_lyric_grounding": ready_count,
            "patch_first": sum(1 for record in records if record["queue_status"]["priority"] == "patch_first"),
            "review_first": sum(1 for record in records if record["queue_status"]["priority"] == "review_first"),
            "skipped": len(skipped),
        },
        "skipped": skipped,
        "outputs": {
            "jsonl": str(jsonl_path),
            "records_dir": str(records_dir),
        },
    }
    manifest_path = write_json(output_root / "lyric_technique_acquisition_manifest.json", manifest)
    manifest["manifest_path"] = str(manifest_path)
    return manifest
