from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .training_data import write_json


def _safe_text(value: Any) -> str:
    return str(value or "").strip()


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _non_generic_count(values: list[str]) -> int:
    blocked = {
        "",
        "unknown",
        "undetermined",
        "unresolved",
        "missing",
        "none",
        "platform-agnostic arrangement",
        "synthetic voice presentation",
        "synthetic vocal framing",
        "general synthetic-pop texture",
        "metadata-derived texture estimate",
        "instrumentation unresolved at metadata-only stage",
        "chorus-lift behavior unresolved",
    }
    count = 0
    seen: set[str] = set()
    for value in values:
        text = _safe_text(value)
        if not text or text.lower() in blocked or text in blocked or text in seen:
            continue
        seen.add(text)
        count += 1
    return count


def _collect_sound_signals(record: dict[str, Any]) -> int:
    sound = record.get("sound_profile", {})
    return _non_generic_count([
        *sound.get("groove_profile", []),
        *sound.get("arrangement_profile", []),
        *sound.get("instrumentation_profile", []),
        *sound.get("texture_profile", []),
        *sound.get("vocal_profile", []),
        *sound.get("sound_anchors", {}).get("positive", []),
        *sound.get("sound_anchors", {}).get("negative", []),
        *sound.get("producer_sound_markers", []),
    ])


def _collect_lyric_signals(record: dict[str, Any]) -> int:
    lyric = record.get("lyric_profile", {})
    return _non_generic_count([
        *lyric.get("section_behavior", []),
        *lyric.get("hook_behavior", []),
        *lyric.get("emotional_arc", []),
        *lyric.get("imagery_bank", []),
        *lyric.get("surface_profile", []),
    ])


def _classify_record(record: dict[str, Any]) -> dict[str, Any]:
    identity = record.get("track_identity", {})
    source_status = record.get("source_status", {})
    prompt_readiness = record.get("prompt_readiness", {})
    reasons: list[str] = []

    lyric_quality = _safe_text(source_status.get("lyric_technique_quality"))
    sound_quality = _safe_text(source_status.get("sound_profile_quality"))
    prompt_ready = bool(prompt_readiness.get("suno_prompt_ready"))
    joinable = lyric_quality == "reviewed"
    lyric_signals = _collect_lyric_signals(record)
    sound_signals = _collect_sound_signals(record)

    production_candidate = False
    professional_target = False
    quality_level = "metadata_only"

    if joinable:
        quality_level = "joinable"
    else:
        reasons.append("lyric_technique_not_joined")

    if prompt_ready:
        quality_level = "prompt_ready"
    else:
        reasons.extend([_safe_text(item) for item in prompt_readiness.get("blocking_reasons", []) if _safe_text(item)])

    if prompt_ready and lyric_signals >= 8 and sound_signals >= 10 and sound_quality in {"partial", "reviewed"}:
        production_candidate = True
        quality_level = "production_candidate"
    else:
        if lyric_signals < 8:
            reasons.append("lyric_signal_density_low")
        if sound_signals < 10:
            reasons.append("sound_signal_density_low")
        if sound_quality not in {"partial", "reviewed"}:
            reasons.append("sound_profile_not_ready")

    if production_candidate and lyric_signals >= 12 and sound_signals >= 14 and sound_quality == "reviewed":
        professional_target = True
        quality_level = "professional_target"
    else:
        if production_candidate and sound_quality != "reviewed":
            reasons.append("sound_profile_not_reviewed")
        if production_candidate and lyric_signals < 12:
            reasons.append("lyric_signal_density_below_professional_target")
        if production_candidate and sound_signals < 14:
            reasons.append("sound_signal_density_below_professional_target")

    deduped_reasons: list[str] = []
    seen: set[str] = set()
    for reason in reasons:
        if reason and reason not in seen:
            seen.add(reason)
            deduped_reasons.append(reason)

    return {
        "track_id": _safe_text(identity.get("track_id")),
        "artist_id": _safe_text(identity.get("artist_id")) or "unknown_artist",
        "quality_level": quality_level,
        "joinable": joinable,
        "prompt_ready": prompt_ready,
        "production_candidate": production_candidate,
        "professional_target": professional_target,
        "reasons": deduped_reasons,
    }


def audit_generation_readiness(
    *,
    generation_root: Path,
    output_root: Path,
) -> dict[str, Any]:
    generation_root = generation_root.resolve()
    output_root = output_root.resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    records_dir = generation_root / "records"

    rows: list[dict[str, Any]] = []
    for path in sorted(records_dir.glob("*.json")):
        try:
            record = _load_json(path)
        except Exception:
            continue
        rows.append(_classify_record(record))

    quality_distribution = {
        level: sum(1 for row in rows if row["quality_level"] == level)
        for level in [
            "metadata_only",
            "joinable",
            "prompt_ready",
            "production_candidate",
            "professional_target",
        ]
    }

    manifest = {
        "schema_version": "1.0",
        "record_type": "generation_readiness_audit",
        "inputs": {
            "generation_root": str(generation_root),
        },
        "counts": {
            "records": len(rows),
            "joinable": sum(1 for row in rows if row["joinable"]),
            "prompt_ready": sum(1 for row in rows if row["prompt_ready"]),
            "production_candidate": sum(1 for row in rows if row["production_candidate"]),
            "professional_target": sum(1 for row in rows if row["professional_target"]),
        },
        "quality_distribution": quality_distribution,
        "records": rows,
    }
    manifest_path = write_json(output_root / "generation_readiness_audit.json", manifest)
    manifest["manifest_path"] = str(manifest_path)
    return manifest
