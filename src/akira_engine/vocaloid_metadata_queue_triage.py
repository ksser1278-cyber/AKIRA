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


def auto_triage_vocaloid_metadata_queue(*, queue_root: Path) -> dict[str, Any]:
    queue_root = queue_root.resolve()
    manifest_path = queue_root / "queue_manifest.json"
    manifest = _load_json(manifest_path)

    rejected_dir = Path(manifest["queue_dirs"]["rejected"]).resolve()
    needs_patch_dir = Path(manifest["queue_dirs"]["needs_patch"]).resolve()

    triaged: list[dict[str, Any]] = []
    counts = {
        "rejected": 0,
        "needs_patch": 0,
        "unchanged": 0,
    }

    for record in manifest.get("records", []):
        track_id = _safe_text(record.get("track_id"))
        auto_status = _safe_text(record.get("auto_status"))
        flags = list(record.get("flags", []))
        source_path = Path(record["queue_path"]).resolve()

        decision = "unchanged"
        destination_path = ""

        if auto_status == "low_confidence":
            destination = rejected_dir / source_path.name
            if _copy_if_exists(source_path, destination):
                decision = "rejected"
                destination_path = str(destination)
        elif auto_status == "needs_manual_review" and flags and set(flags) == {"source:missing_original_upload_url"}:
            destination = needs_patch_dir / source_path.name
            if _copy_if_exists(source_path, destination):
                decision = "needs_patch"
                destination_path = str(destination)

        counts[decision] += 1
        triaged.append(
            {
                "track_id": track_id,
                "auto_status": auto_status,
                "flags": flags,
                "decision": decision,
                "source_path": str(source_path),
                "destination_path": destination_path,
            }
        )

    triage_manifest = {
        "schema_version": "1.0",
        "record_type": "vocaloid_metadata_queue_triage_manifest",
        "queue_root": str(queue_root),
        "queue_manifest_path": str(manifest_path),
        "counts": counts,
        "records": triaged,
    }
    triage_manifest_path = write_json(queue_root / "triage_manifest.json", triage_manifest)
    triage_manifest["manifest_path"] = str(triage_manifest_path)
    return triage_manifest
