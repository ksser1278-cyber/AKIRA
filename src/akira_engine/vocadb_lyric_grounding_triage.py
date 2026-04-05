from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .training_data import write_json


DEFERRED_TITLE_MARKERS = (
    "\u30c7\u30e2\u30bd\u30f3\u30b0",
    "\u8a66\u8074\u7248",
    "demo song",
    "preview",
    "crossfade",
    "short ver",
)


def _safe_text(value: Any) -> str:
    return str(value or "").strip()


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _is_deferred_grounding_record(record: dict[str, Any]) -> bool:
    title = _safe_text(record.get("track_identity", {}).get("title")).lower()
    producer = _safe_text(record.get("metadata_context", {}).get("producer")).lower()
    if any(marker.lower() in title for marker in DEFERRED_TITLE_MARKERS):
        return True
    if "synthesizer v" in title and ("demo" in title or "\u8a66\u8074" in title):
        return True
    if "demo" in producer:
        return True
    return False


def auto_triage_vocadb_lyric_grounding_workspace(
    *,
    workspace_root: Path,
) -> dict[str, Any]:
    workspace_root = workspace_root.resolve()
    incoming_dir = workspace_root / "incoming"
    rejected_dir = workspace_root / "rejected"
    rejected_dir.mkdir(parents=True, exist_ok=True)

    rejected: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    for path in sorted(incoming_dir.glob("vocadb_*.json")):
        record = _load_json(path)
        track_id = _safe_text(record.get("track_identity", {}).get("track_id")) or path.stem
        title = _safe_text(record.get("track_identity", {}).get("title"))
        if not _is_deferred_grounding_record(record):
            skipped.append({"track_id": track_id, "reason": "not_deferred"})
            continue

        record["grounding_review"] = {
            "grounding_status": "rejected",
            "review_notes": "Auto-rejected from lyric grounding lane because the title indicates a demo/preview/non-final artifact.",
        }
        rejected_path = rejected_dir / path.name
        write_json(rejected_path, record)
        path.unlink()
        rejected.append(
            {
                "track_id": track_id,
                "title": title,
                "rejected_record_path": str(rejected_path),
            }
        )

    manifest = {
        "schema_version": "1.0",
        "record_type": "vocadb_lyric_grounding_triage_manifest",
        "workspace_root": str(workspace_root),
        "counts": {
            "rejected": len(rejected),
            "skipped": len(skipped),
        },
        "rejected": rejected,
        "skipped": skipped,
    }
    manifest_path = write_json(workspace_root / "vocadb_lyric_grounding_triage_manifest.json", manifest)
    manifest["manifest_path"] = str(manifest_path)
    return manifest


def defer_vocadb_lyric_grounding_records(
    *,
    workspace_root: Path,
    track_ids: list[str],
    review_notes: str,
) -> dict[str, Any]:
    workspace_root = workspace_root.resolve()
    incoming_dir = workspace_root / "incoming"
    needs_patch_dir = workspace_root / "needs_patch"
    needs_patch_dir.mkdir(parents=True, exist_ok=True)

    deferred: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    requested = {track_id for track_id in track_ids if _safe_text(track_id)}

    for track_id in sorted(requested):
        path = incoming_dir / f"{track_id}.json"
        if not path.exists():
            skipped.append({"track_id": track_id, "reason": "missing_incoming_record"})
            continue
        record = _load_json(path)
        record["grounding_review"] = {
            "grounding_status": "needs_patch",
            "review_notes": review_notes,
        }
        deferred_path = needs_patch_dir / path.name
        write_json(deferred_path, record)
        path.unlink()
        deferred.append({"track_id": track_id, "needs_patch_record_path": str(deferred_path)})

    manifest = {
        "schema_version": "1.0",
        "record_type": "vocadb_lyric_grounding_defer_manifest",
        "workspace_root": str(workspace_root),
        "counts": {
            "deferred": len(deferred),
            "skipped": len(skipped),
        },
        "deferred": deferred,
        "skipped": skipped,
    }
    manifest_path = write_json(workspace_root / "vocadb_lyric_grounding_defer_manifest.json", manifest)
    manifest["manifest_path"] = str(manifest_path)
    return manifest
