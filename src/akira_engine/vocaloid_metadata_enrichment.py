from __future__ import annotations

import json
import urllib.request
from pathlib import Path
from typing import Any

from .training_data import write_json


VOCADB_API_ROOT = "https://vocadb.net/api"
VOCADB_USER_AGENT = "AKIRA-ENGINE/1.0 vocaloid-metadata-enrichment"


def _safe_text(value: Any) -> str:
    return str(value or "").strip()


def _vocadb_song_detail(song_id: int) -> dict[str, Any]:
    url = f"{VOCADB_API_ROOT}/songs/{song_id}?fields=WebLinks,PVs"
    request = urllib.request.Request(url, headers={"User-Agent": VOCADB_USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def _platform_from_url(url: str) -> str:
    lowered = url.lower()
    if "youtu" in lowered:
        return "youtube"
    if "nicovideo.jp" in lowered or "nico.ms" in lowered:
        return "niconico"
    if "bilibili" in lowered:
        return "bilibili"
    if "bandcamp" in lowered:
        return "other"
    if "spotify" in lowered or "apple.com" in lowered or "music.apple" in lowered:
        return "streaming"
    return "other"


def _has_official_upload(record: dict[str, Any]) -> bool:
    return any(_safe_text(source.get("source_type")) == "official_upload" for source in record.get("metadata_sources", []))


def _pick_official_upload(detail: dict[str, Any]) -> tuple[str, str] | None:
    for pv in detail.get("pvs", []) or []:
        pv_type = _safe_text(pv.get("pvType")).lower()
        if pv_type not in {"original", "other"}:
            continue
        url = _safe_text(pv.get("url"))
        if not url:
            continue
        service = _safe_text(pv.get("service")) or "Original upload"
        return url, service
    for link in detail.get("webLinks", []) or []:
        category = _safe_text(link.get("category")).lower()
        url = _safe_text(link.get("url"))
        if category != "official" or not url:
            continue
        description = _safe_text(link.get("description")) or "Official link"
        return url, description
    return None


def enrich_vocaloid_metadata_intake(*, intake_dir: Path) -> dict[str, Any]:
    intake_dir = intake_dir.resolve()
    enriched_records: list[dict[str, Any]] = []
    skipped_records: list[dict[str, Any]] = []

    for path in sorted(intake_dir.glob("vocadb_*.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        if _safe_text(record.get("record_type")) != "vocaloid_metadata_record":
            continue

        track_id = _safe_text(record.get("track_identity", {}).get("track_id"))
        if _has_official_upload(record):
            skipped_records.append({"track_id": track_id, "reason": "already_has_official_upload", "path": str(path)})
            continue

        song_id_text = track_id.removeprefix("vocadb_")
        if not song_id_text.isdigit():
            skipped_records.append({"track_id": track_id, "reason": "invalid_track_id", "path": str(path)})
            continue

        detail = _vocadb_song_detail(int(song_id_text))
        candidate = _pick_official_upload(detail)
        if candidate is None:
            skipped_records.append({"track_id": track_id, "reason": "no_official_upload_candidate", "path": str(path)})
            continue

        url, label_hint = candidate
        record.setdefault("metadata_sources", []).append(
            {
                "label": f"Original upload ({label_hint})",
                "source_type": "official_upload",
                "url": url,
                "notes": "Enriched from VocaDB song detail.",
            }
        )
        release_context = record.setdefault("release_context", {})
        if _safe_text(release_context.get("original_platform")) in {"", "unknown"}:
            release_context["original_platform"] = _platform_from_url(url)
        collection_status = record.setdefault("collection_status", {})
        note = _safe_text(collection_status.get("notes"))
        suffix = "Official upload source enriched from VocaDB detail."
        collection_status["notes"] = f"{note} {suffix}".strip() if note else suffix
        write_json(path, record)
        enriched_records.append({"track_id": track_id, "path": str(path), "official_upload_url": url})

    manifest = {
        "schema_version": "1.0",
        "record_type": "vocaloid_metadata_enrichment_manifest",
        "intake_dir": str(intake_dir),
        "counts": {
            "enriched_records": len(enriched_records),
            "skipped_records": len(skipped_records),
        },
        "enriched_records": enriched_records,
        "skipped_records": skipped_records,
    }
    manifest_path = write_json(intake_dir / "vocadb_enrichment_manifest.json", manifest)
    manifest["manifest_path"] = str(manifest_path)
    return manifest
