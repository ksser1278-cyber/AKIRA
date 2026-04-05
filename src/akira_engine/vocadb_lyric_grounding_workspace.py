from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .training_data import write_json


def _safe_text(value: Any) -> str:
    return str(value or "").strip()


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _record_template(queue_record: dict[str, Any], workspace_root: Path) -> dict[str, Any]:
    track = queue_record.get("track_identity", {})
    sources = queue_record.get("acquisition_sources", {})
    meta = queue_record.get("metadata_context", {})
    track_id = _safe_text(track.get("track_id"))
    return {
        "schema_version": "1.0",
        "record_type": "vocadb_lyric_grounding_record",
        "track_identity": {
            "track_id": track_id,
            "artist_id": _safe_text(track.get("artist_id")),
            "title": _safe_text(track.get("canonical_title")),
        },
        "grounding_sources": {
            "vocadb_page": _safe_text((sources.get("vocadb_pages") or [""])[0]),
            "official_uploads": sources.get("official_uploads", []),
            "lyric_sources": []
        },
        "content_assets": {
            "lyric_text_ref": f"lyric_assets/{track_id}.txt",
            "section_map_ref": f"section_maps/{track_id}.sections.json",
            "notes": "Fill lyric text and section map using grounded Japanese source evidence. Keep vocadb track id stable."
        },
        "grounding_review": {
            "grounding_status": "incoming",
            "review_notes": _safe_text(queue_record.get("queue_status", {}).get("next_step")),
        },
        "metadata_context": {
            "producer": _safe_text(meta.get("producer")),
            "engine_family": _safe_text(meta.get("engine_family")),
            "voicebanks": meta.get("voicebanks", []),
            "original_platform": _safe_text(meta.get("original_platform")),
            "original_upload_date": _safe_text(meta.get("original_upload_date")),
        },
    }


def build_vocadb_lyric_grounding_workspace(
    *,
    queue_root: Path,
    workspace_root: Path,
) -> dict[str, Any]:
    queue_root = queue_root.resolve()
    workspace_root = workspace_root.resolve()
    incoming_dir = workspace_root / "incoming"
    accepted_dir = workspace_root / "accepted"
    rejected_dir = workspace_root / "rejected"
    needs_patch_dir = workspace_root / "needs_patch"
    lyric_assets_dir = workspace_root / "lyric_assets"
    section_maps_dir = workspace_root / "section_maps"
    for directory in [incoming_dir, accepted_dir, rejected_dir, needs_patch_dir, lyric_assets_dir, section_maps_dir]:
        directory.mkdir(parents=True, exist_ok=True)

    queue_records_dir = queue_root / "records"
    written = 0
    skipped = 0
    for path in sorted(queue_records_dir.glob("vocadb_*.json")):
        try:
            queue_record = _load_json(path)
        except Exception:
            skipped += 1
            continue
        template = _record_template(queue_record, workspace_root)
        track_id = _safe_text(template.get("track_identity", {}).get("track_id"))
        if not track_id:
            skipped += 1
            continue
        write_json(incoming_dir / f"{track_id}.json", template)
        lyric_asset_path = lyric_assets_dir / f"{track_id}.txt"
        section_map_path = section_maps_dir / f"{track_id}.sections.json"
        if not lyric_asset_path.exists():
            lyric_asset_path.write_text("", encoding="utf-8")
        if not section_map_path.exists():
            section_map_path.write_text(
                json.dumps({"sections": [], "hook_lines": []}, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        written += 1

    readme = (
        "# VocaDB Lyric Grounding Workspace\n\n"
        "This workspace is seeded from a vocadb track-id aligned acquisition queue.\n\n"
        "Fill `incoming/<track_id>.json`, `lyric_assets/<track_id>.txt`, and `section_maps/<track_id>.sections.json`.\n"
        "Promote reviewed records to `accepted/` once grounded lyric sources and section maps are complete.\n"
    )
    (workspace_root / "README.md").write_text(readme, encoding="utf-8")
    manifest = {
        "schema_version": "1.0",
        "record_type": "vocadb_lyric_grounding_workspace_manifest",
        "queue_root": str(queue_root),
        "workspace_root": str(workspace_root),
        "counts": {
            "written_incoming_records": written,
            "skipped_records": skipped,
        },
    }
    manifest_path = write_json(workspace_root / "workspace_manifest.json", manifest)
    manifest["manifest_path"] = str(manifest_path)
    return manifest
