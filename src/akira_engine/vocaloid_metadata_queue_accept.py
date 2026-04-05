from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .training_data import write_json


def _safe_text(value: Any) -> str:
    return str(value or "").strip()


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _copy_if_exists(source: Path, target: Path) -> bool:
    if not source.exists():
        return False
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    return True


def auto_accept_vocaloid_metadata_queue(*, queue_root: Path) -> dict[str, Any]:
    queue_root = queue_root.resolve()
    manifest_path = queue_root / "queue_manifest.json"
    manifest = _load_json(manifest_path)
    accepted_dir = Path(manifest["queue_dirs"]["accepted"]).resolve()

    accepted_records: list[dict[str, Any]] = []
    skipped_records: list[dict[str, Any]] = []

    for record in manifest.get("records", []):
        auto_status = _safe_text(record.get("auto_status"))
        flags = list(record.get("flags", []))
        source_path = Path(record["queue_path"]).resolve()
        if auto_status != "review_candidate" or flags:
            skipped_records.append(
                {
                    "track_id": _safe_text(record.get("track_id")),
                    "reason": f"status:{auto_status}" if auto_status != "review_candidate" else "flags_present",
                    "source_path": str(source_path),
                }
            )
            continue

        destination = accepted_dir / source_path.name
        if _copy_if_exists(source_path, destination):
            accepted_records.append(
                {
                    "track_id": _safe_text(record.get("track_id")),
                    "canonical_title": _safe_text(record.get("canonical_title")),
                    "producer": _safe_text(record.get("producer")),
                    "source_path": str(source_path),
                    "destination_path": str(destination),
                }
            )

    accept_manifest = {
        "schema_version": "1.0",
        "record_type": "vocaloid_metadata_queue_accept_manifest",
        "queue_root": str(queue_root),
        "queue_manifest_path": str(manifest_path),
        "counts": {
            "accepted": len(accepted_records),
            "skipped": len(skipped_records),
        },
        "accepted_records": accepted_records,
        "skipped_records": skipped_records,
    }
    accept_manifest_path = write_json(queue_root / "accept_manifest.json", accept_manifest)
    accept_manifest["manifest_path"] = str(accept_manifest_path)
    return accept_manifest
