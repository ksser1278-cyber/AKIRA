from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .lyric_technique_extraction import build_lyric_technique_record
from .training_data import write_json, write_jsonl


def _safe_text(value: Any) -> str:
    return str(value or "").strip()


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_grounded_normalized_doc(workspace_root: Path, record: dict[str, Any]) -> dict[str, Any]:
    track = record.get("track_identity", {})
    assets = record.get("content_assets", {})
    lyric_ref = Path(_safe_text(assets.get("lyric_text_ref")))
    section_ref = Path(_safe_text(assets.get("section_map_ref")))
    lyric_path = lyric_ref if lyric_ref.is_absolute() else (workspace_root / lyric_ref).resolve()
    section_path = section_ref if section_ref.is_absolute() else (workspace_root / section_ref).resolve()
    lyric_lines = [line.strip() for line in lyric_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    section_map = _load_json(section_path)
    sections = []
    cursor = 0
    for index, spec in enumerate(section_map.get("sections", [])):
        line_count = int(spec.get("line_count", 0) or 0)
        section_lines = lyric_lines[cursor : cursor + line_count] if line_count > 0 else []
        cursor += line_count
        sections.append(
            {
                "label": _safe_text(spec.get("section")) or f"section_{index + 1}",
                "line_count": len(section_lines),
                "lines": section_lines,
            }
        )
    return {
        "track_id": _safe_text(track.get("track_id")),
        "artist_id": _safe_text(track.get("artist_id")),
        "title": _safe_text(track.get("title")),
        "language": _safe_text(record.get("metadata_context", {}).get("language_hint")) or "ja",
        "source_site": "grounded_vocadb_acquisition",
        "source_family": "grounded_vocadb_acquisition",
        "normalized_text": "\n".join(lyric_lines),
        "sections": sections,
        "hook_lines": [_safe_text(line) for line in section_map.get("hook_lines", []) if _safe_text(line)],
        "stats": {"section_count": len(sections)},
    }


def import_vocadb_grounded_technique_records(
    *,
    workspace_root: Path,
    output_root: Path,
) -> dict[str, Any]:
    workspace_root = workspace_root.resolve()
    output_root = output_root.resolve()
    accepted_dir = workspace_root / "accepted"
    records_dir = output_root / "records"
    records_dir.mkdir(parents=True, exist_ok=True)

    records: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    for path in sorted(accepted_dir.glob("vocadb_*.json")):
        try:
            grounded_record = _load_json(path)
        except Exception as exc:
            skipped.append({"path": str(path), "reason": f"invalid_json:{type(exc).__name__}"})
            continue
        if _safe_text(grounded_record.get("grounding_review", {}).get("grounding_status")) != "accepted":
            skipped.append({"path": str(path), "reason": "grounding_not_accepted"})
            continue
        try:
            normalized_doc = _load_grounded_normalized_doc(workspace_root, grounded_record)
        except Exception as exc:
            skipped.append({"path": str(path), "reason": f"missing_grounded_assets:{type(exc).__name__}"})
            continue
        metadata_context = grounded_record.get("metadata_context", {})
        artist_analysis = {
            "imagery_profile": {"top_imagery_clusters": []},
            "emotional_profile": {"dominant_arc_patterns": []},
            "mode_candidates": [],
            "analysis_notes": [
                "Technique record imported from vocadb track-id aligned grounded lyric acquisition workspace."
            ],
        }
        record = build_lyric_technique_record(
            normalized_doc=normalized_doc,
            artist_analysis=artist_analysis,
            rights_status="grounded_reference_only",
        )
        if _safe_text(metadata_context.get("producer")):
            record["mode_evidence"]["mode_evidence_notes"] = [
                f"Producer context: {_safe_text(metadata_context.get('producer'))}",
                f"Engine family: {_safe_text(metadata_context.get('engine_family'))}",
            ]
        records.append(record)
        write_json(records_dir / f"{record['track_identity']['track_id']}.json", record)

    jsonl_path = write_jsonl(output_root / "lyric_technique_records.jsonl", records)
    manifest = {
        "schema_version": "1.0",
        "record_type": "vocadb_grounded_technique_import_manifest",
        "workspace_root": str(workspace_root),
        "output_root": str(output_root),
        "counts": {
            "records": len(records),
            "skipped": len(skipped),
        },
        "skipped": skipped,
        "outputs": {
            "jsonl": str(jsonl_path),
            "records_dir": str(records_dir),
        },
    }
    manifest_path = write_json(output_root / "lyric_technique_manifest.json", manifest)
    manifest["manifest_path"] = str(manifest_path)
    return manifest
