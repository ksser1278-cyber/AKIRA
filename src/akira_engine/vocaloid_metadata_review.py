from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from .training_data import write_json


def _safe_text(value: Any) -> str:
    return str(value or "").strip()


def _looks_like_placeholder_title(title: str) -> bool:
    lowered = title.lower()
    if lowered.startswith("vocadb_song_"):
        return True
    if title in {"1", "?"}:
        return True
    if "\ufffd" in title or "?" in title:
        return True
    return False


def _contains_variant_hint(title: str) -> bool:
    lowered = title.lower()
    hints = ["remix", "cover", "short ver.", "medley", "instrumental", "inst."]
    return any(hint in lowered for hint in hints)


def _review_record(record: dict[str, Any]) -> dict[str, Any]:
    title = _safe_text(record.get("track_identity", {}).get("canonical_title"))
    producer = _safe_text(record.get("credits", {}).get("producer"))
    voicebanks = record.get("vocal_synthesis", {}).get("voicebanks", [])
    metadata_sources = record.get("metadata_sources", [])
    source_urls = [item.get("url", "") for item in metadata_sources]

    flags: list[str] = []
    if _looks_like_placeholder_title(title):
        flags.append("title:placeholder_or_corrupted")
    if _contains_variant_hint(title):
        flags.append("title:variant_hint")
    if producer == "unknown":
        flags.append("credits:unknown_producer")
    if not voicebanks or voicebanks == ["unknown"]:
        flags.append("vocal:unknown_voicebank")
    if not any("vocadb.net/S/" in url for url in source_urls):
        flags.append("source:missing_vocadb_song_page")
    if not any(_safe_text(item.get("source_type")) == "official_upload" for item in metadata_sources):
        flags.append("source:missing_original_upload_url")

    auto_status = "review_candidate"
    if flags:
        auto_status = "needs_manual_review"
    if any(flag in flags for flag in ["title:placeholder_or_corrupted", "title:variant_hint"]):
        auto_status = "low_confidence"

    return {
        "track_id": _safe_text(record.get("track_identity", {}).get("track_id")),
        "canonical_title": title,
        "producer": producer,
        "auto_status": auto_status,
        "flags": flags,
    }


def review_vocaloid_metadata_intake(*, intake_dir: Path, output_dir: Path) -> dict[str, Any]:
    intake_dir = intake_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    review_rows: list[dict[str, Any]] = []
    flag_counts: Counter[str] = Counter()
    status_counts: Counter[str] = Counter()

    for path in sorted(intake_dir.glob("vocadb_*.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        if _safe_text(record.get("record_type")) != "vocaloid_metadata_record":
            continue
        review = _review_record(record)
        review["path"] = str(path)
        review_rows.append(review)
        status_counts[review["auto_status"]] += 1
        for flag in review["flags"]:
            flag_counts[flag] += 1

    manifest = {
        "schema_version": "1.0",
        "record_type": "vocaloid_metadata_review_manifest",
        "intake_dir": str(intake_dir),
        "output_dir": str(output_dir.resolve()),
        "counts": {
            "records": len(review_rows),
            "review_candidate": status_counts.get("review_candidate", 0),
            "needs_manual_review": status_counts.get("needs_manual_review", 0),
            "low_confidence": status_counts.get("low_confidence", 0),
        },
        "flag_summary": dict(flag_counts),
        "records": review_rows,
    }
    manifest_path = write_json(output_dir / "vocaloid_metadata_review_manifest.json", manifest)
    manifest["manifest_path"] = str(manifest_path)
    return manifest
