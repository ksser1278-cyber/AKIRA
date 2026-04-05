from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .training_data import write_json


def _safe_text(value: Any) -> str:
    return str(value or "").strip()


def _track_ids_from_jsonl(path: Path, key_path: list[str]) -> set[str]:
    ids: set[str] = set()
    if not path.exists():
        return ids
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except Exception:
            continue
        current: Any = payload
        for key in key_path:
            current = current.get(key, {}) if isinstance(current, dict) else {}
        text = _safe_text(current)
        if text:
            ids.add(text)
    return ids


def audit_generation_joinability(
    *,
    generation_jsonl: Path,
    technique_jsonl: Path,
    output_root: Path,
) -> dict[str, Any]:
    generation_jsonl = generation_jsonl.resolve()
    technique_jsonl = technique_jsonl.resolve()
    output_root = output_root.resolve()
    output_root.mkdir(parents=True, exist_ok=True)

    generation_ids = _track_ids_from_jsonl(generation_jsonl, ["track_identity", "track_id"])
    technique_ids = _track_ids_from_jsonl(technique_jsonl, ["track_identity", "track_id"])
    overlap_ids = sorted(generation_ids & technique_ids)
    generation_only = sorted(generation_ids - technique_ids)
    technique_only = sorted(technique_ids - generation_ids)

    manifest = {
        "schema_version": "1.0",
        "record_type": "generation_joinability_audit",
        "inputs": {
            "generation_jsonl": str(generation_jsonl),
            "technique_jsonl": str(technique_jsonl),
        },
        "counts": {
            "generation_tracks": len(generation_ids),
            "technique_tracks": len(technique_ids),
            "overlap_tracks": len(overlap_ids),
            "generation_only_tracks": len(generation_only),
            "technique_only_tracks": len(technique_only),
        },
        "joinability": {
            "has_overlap": bool(overlap_ids),
            "status": "joinable" if overlap_ids else "blocked_no_track_id_overlap",
            "notes": (
                "Generation and technique corpora share track ids and can be merged directly."
                if overlap_ids
                else "Generation and technique corpora do not share track ids. Build or map a common corpus before merge."
            ),
        },
        "samples": {
            "overlap_tracks": overlap_ids[:25],
            "generation_only_tracks": generation_only[:25],
            "technique_only_tracks": technique_only[:25],
        },
    }
    manifest_path = write_json(output_root / "generation_joinability_audit.json", manifest)
    manifest["manifest_path"] = str(manifest_path)
    return manifest
