from __future__ import annotations

import json
import re
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any

from .training_data import write_json


def _safe_text(value: Any) -> str:
    return str(value or "").strip()


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _title_weak(title: str) -> bool:
    return (not title) or ("\ufffd" in title) or ("??" in title) or (title in {"?", "1"})


def _looks_opaque_short_text(text: str) -> bool:
    cleaned = re.sub(r"[\s\-\_\.\,\!\?\#\(\)\[\]\"'/:;]+", "", _safe_text(text))
    if len(cleaned) < 2 or len(cleaned) > 8:
        return False
    has_hiragana = any("\u3040" <= ch <= "\u309f" for ch in cleaned)
    has_katakana = any("\u30a0" <= ch <= "\u30ff" for ch in cleaned)
    has_latin = any(ch.isascii() and ch.isalpha() for ch in cleaned)
    has_digit = any(ch.isdigit() for ch in cleaned)
    if has_hiragana or has_katakana or has_latin or has_digit:
        return False
    try:
        return all("CJK UNIFIED IDEOGRAPH" in unicodedata.name(ch) for ch in cleaned)
    except ValueError:
        return False


def _variant_preferred(record: dict[str, Any]) -> bool:
    canonical = _safe_text(record.get("track_identity", {}).get("canonical_title"))
    variants = [_safe_text(item) for item in record.get("track_identity", {}).get("title_variants", []) if _safe_text(item)]
    if not canonical or not variants:
        return False
    canonical_ascii = sum(1 for ch in canonical if ch.isascii() and (ch.isalpha() or ch.isdigit()))
    best_variant_ascii = max(
        (sum(1 for ch in variant if ch.isascii() and (ch.isalpha() or ch.isdigit())) for variant in variants),
        default=0,
    )
    return best_variant_ascii >= canonical_ascii + 4


def _variant_heavy(record: dict[str, Any]) -> bool:
    relations = record.get("release_context", {}).get("variant_relations", []) or []
    if len(relations) >= 2:
        return True
    title = _safe_text(record.get("track_identity", {}).get("canonical_title")).lower()
    return any(token in title for token in ["remix", "cover", "short ver.", "inst.", "instrumental", "remake"])


def _classify_record(record: dict[str, Any]) -> tuple[str, list[str]]:
    flags: list[str] = []
    title = _safe_text(record.get("track_identity", {}).get("canonical_title"))
    producer = _safe_text(record.get("credits", {}).get("producer"))
    voicebanks = [_safe_text(item) for item in record.get("vocal_synthesis", {}).get("voicebanks", []) if _safe_text(item)]
    metadata_sources = record.get("metadata_sources", []) or []
    source_types = {_safe_text(item.get("source_type")) for item in metadata_sources}

    if _title_weak(title):
        flags.append("title:weak")
    if _looks_opaque_short_text(title):
        flags.append("title:opaque_short_text")
    if _variant_preferred(record):
        flags.append("title:variant_preferred")
    if not producer or producer == "unknown":
        flags.append("credits:weak_producer")
    if not voicebanks or voicebanks == ["unknown"]:
        flags.append("vocal:weak_voicebank")
    if "official_upload" not in source_types:
        flags.append("source:missing_official_upload")
    if len(metadata_sources) < 2:
        flags.append("source:thin_basis")
    if _variant_heavy(record):
        flags.append("variant:ambiguous")

    if any(flag in flags for flag in ["title:weak", "credits:weak_producer", "title:opaque_short_text"]) and len(flags) >= 3:
        return "deferred", flags
    if any(
        flag in flags
        for flag in [
            "title:weak",
            "title:opaque_short_text",
            "title:variant_preferred",
            "source:missing_official_upload",
            "variant:ambiguous",
        ]
    ):
        return "low_value_retained", flags
    if flags:
        return "supporting", flags
    return "core", flags


def classify_corpus_value(
    *,
    corpus_root: Path,
    output_root: Path,
    write_back: bool = False,
) -> dict[str, Any]:
    corpus_root = corpus_root.resolve()
    output_root = output_root.resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    accepted_dir = corpus_root / "accepted"

    rows: list[dict[str, Any]] = []
    tier_counts: Counter[str] = Counter()
    flag_counts: Counter[str] = Counter()

    for path in sorted(accepted_dir.glob("vocadb_*.json")):
        try:
            record = _load_json(path)
        except Exception:
            continue
        tier, flags = _classify_record(record)
        tier_counts[tier] += 1
        for flag in flags:
            flag_counts[flag] += 1
        if write_back:
            status = record.setdefault("collection_status", {})
            status["corpus_value_tier"] = tier
            status["value_flags"] = flags
            path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        rows.append(
            {
                "track_id": _safe_text(record.get("track_identity", {}).get("track_id")),
                "canonical_title": _safe_text(record.get("track_identity", {}).get("canonical_title")),
                "producer": _safe_text(record.get("credits", {}).get("producer")),
                "corpus_value_tier": tier,
                "value_flags": flags,
                "path": str(path),
            }
        )

    manifest = {
        "schema_version": "1.0",
        "record_type": "corpus_value_classification",
        "inputs": {
            "corpus_root": str(corpus_root),
            "write_back": write_back,
        },
        "counts": {
            "records": len(rows),
            "core": tier_counts.get("core", 0),
            "supporting": tier_counts.get("supporting", 0),
            "low_value_retained": tier_counts.get("low_value_retained", 0),
            "deferred": tier_counts.get("deferred", 0),
        },
        "flag_summary": dict(flag_counts),
        "records": rows,
    }
    manifest_path = write_json(output_root / "corpus_value_classification.json", manifest)
    manifest["manifest_path"] = str(manifest_path)
    return manifest
