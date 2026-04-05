from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .training_data import write_json


def _safe_text(value: Any) -> str:
    return str(value or "").strip()


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_vocaloid_metadata_canonical_corpus(*, queue_root: Path, output_root: Path) -> dict[str, Any]:
    queue_root = queue_root.resolve()
    output_root = output_root.resolve()
    accept_manifest_path = queue_root / "accept_manifest.json"
    accept_manifest = _load_json(accept_manifest_path)
    accepted_dir = output_root / "accepted"
    accepted_dir.mkdir(parents=True, exist_ok=True)

    canonical_records: list[dict[str, Any]] = []
    for record in accept_manifest.get("accepted_records", []):
        source_path = Path(record["destination_path"]).resolve()
        if not source_path.exists():
            continue
        payload = json.loads(source_path.read_text(encoding="utf-8"))
        payload.setdefault("collection_status", {})
        payload["collection_status"]["canonical_review_status"] = "accepted"
        payload["collection_status"]["metadata_quality"] = "reviewed"
        existing_note = _safe_text(payload["collection_status"].get("notes"))
        suffix = "Promoted from zero-flag review_candidate via queue auto-accept."
        payload["collection_status"]["notes"] = f"{existing_note} {suffix}".strip() if existing_note else suffix
        target_path = accepted_dir / source_path.name
        target_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        canonical_records.append(
            {
                "track_id": _safe_text(payload.get("track_identity", {}).get("track_id")),
                "canonical_title": _safe_text(payload.get("track_identity", {}).get("canonical_title")),
                "producer": _safe_text(payload.get("credits", {}).get("producer")),
                "path": str(target_path),
            }
        )

    manifest = {
        "schema_version": "1.0",
        "record_type": "vocaloid_metadata_canonical_manifest",
        "queue_root": str(queue_root),
        "accept_manifest_path": str(accept_manifest_path),
        "output_root": str(output_root),
        "counts": {
            "accepted_records": len(canonical_records),
        },
        "records": canonical_records,
    }
    manifest_path = write_json(output_root / "canonical_manifest.json", manifest)
    manifest["manifest_path"] = str(manifest_path)
    return manifest
