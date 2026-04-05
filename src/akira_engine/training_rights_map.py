from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ALLOWED_RIGHTS_STATUSES = {
    "cleared_for_training",
    "licensed_for_training",
    "internal_only_holdout",
    "not_cleared",
    "unknown",
}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            text = line.strip()
            if not text:
                continue
            rows.append(json.loads(text))
    return rows


def _safe_text(value: Any) -> str:
    return str(value or "").strip()


def load_rights_map(path: Path | None) -> dict[str, dict[str, Any]]:
    if path is None or not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    records = payload.get("records", []) if isinstance(payload, dict) else []
    out: dict[str, dict[str, Any]] = {}
    for row in records:
        if not isinstance(row, dict):
            continue
        track_id = _safe_text(row.get("track_id"))
        if not track_id:
            continue
        rights_status = _safe_text(row.get("rights_status")) or "unknown"
        if rights_status not in ALLOWED_RIGHTS_STATUSES:
            rights_status = "unknown"
        out[track_id] = {
            "track_id": track_id,
            "artist_id": _safe_text(row.get("artist_id")),
            "rights_status": rights_status,
            "source_basis": _safe_text(row.get("source_basis")),
            "notes": _safe_text(row.get("notes")),
        }
    return out


def bootstrap_training_rights_map(
    *,
    derived_jsonl: Path,
    existing_map_path: Path | None = None,
    updated_at: str,
) -> dict[str, Any]:
    existing = load_rights_map(existing_map_path)
    rows = load_jsonl(derived_jsonl)

    for row in rows:
        track_id = _safe_text(row.get("track_id"))
        artist_id = _safe_text(row.get("artist_id"))
        if not track_id:
            continue
        if track_id not in existing:
            existing[track_id] = {
                "track_id": track_id,
                "artist_id": artist_id,
                "rights_status": "unknown",
                "source_basis": "",
                "notes": "Bootstrap placeholder. Resolve before supervised export.",
            }
        elif artist_id and not existing[track_id].get("artist_id"):
            existing[track_id]["artist_id"] = artist_id

    records = sorted(
        existing.values(),
        key=lambda item: (item.get("artist_id", ""), item.get("track_id", "")),
    )
    return {
        "schema_version": "1.0",
        "updated_at": updated_at,
        "records": records,
    }
