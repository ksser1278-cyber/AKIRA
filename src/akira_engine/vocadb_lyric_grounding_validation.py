from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .training_data import write_json


def _safe_text(value: Any) -> str:
    return str(value or "").strip()


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _is_broken_text(text: str) -> bool:
    return ("\ufffd" in text) or ("??" in text)


def _validate_record(workspace_root: Path, record_path: Path) -> dict[str, Any]:
    record = _load_json(record_path)
    track = record.get("track_identity", {})
    sources = record.get("grounding_sources", {})
    assets = record.get("content_assets", {})
    review = record.get("grounding_review", {})
    track_id = _safe_text(track.get("track_id"))
    lyric_ref = Path(_safe_text(assets.get("lyric_text_ref")))
    section_ref = Path(_safe_text(assets.get("section_map_ref")))
    lyric_path = lyric_ref if lyric_ref.is_absolute() else (workspace_root / lyric_ref).resolve()
    section_path = section_ref if section_ref.is_absolute() else (workspace_root / section_ref).resolve()

    issues: list[str] = []
    if not track_id:
        issues.append("missing_track_id")
    if not _safe_text(track.get("artist_id")):
        issues.append("missing_artist_id")
    if not _safe_text(track.get("title")):
        issues.append("missing_title")
    if not _safe_text(sources.get("vocadb_page")):
        issues.append("missing_vocadb_page")
    if not sources.get("official_uploads"):
        issues.append("missing_official_upload")
    if not sources.get("lyric_sources"):
        issues.append("missing_lyric_sources")
    if not lyric_path.exists():
        issues.append("missing_lyric_asset")
        lyric_lines: list[str] = []
    else:
        lyric_lines = [line.strip() for line in lyric_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        if not lyric_lines:
            issues.append("empty_lyric_asset")
        if any(_is_broken_text(line) for line in lyric_lines):
            issues.append("broken_lyric_text")
    if not section_path.exists():
        issues.append("missing_section_map")
        section_map = {"sections": [], "hook_lines": []}
    else:
        section_map = _load_json(section_path)
    sections = section_map.get("sections", [])
    hook_lines = [_safe_text(line) for line in section_map.get("hook_lines", []) if _safe_text(line)]
    if not sections:
        issues.append("missing_sections")
    total_line_count = sum(int(item.get("line_count", 0) or 0) for item in sections)
    if lyric_lines and total_line_count != len(lyric_lines):
        issues.append("section_line_count_mismatch")
    if not hook_lines:
        issues.append("missing_hook_lines")
    if any(_is_broken_text(_safe_text(line)) for line in hook_lines):
        issues.append("broken_hook_lines")
    grounding_status = _safe_text(review.get("grounding_status")) or "incoming"
    is_valid = not issues
    return {
        "track_id": track_id or record_path.stem,
        "record_path": str(record_path),
        "grounding_status": grounding_status,
        "valid": is_valid,
        "issues": issues,
        "counts": {
            "lyric_lines": len(lyric_lines),
            "sections": len(sections),
            "hook_lines": len(hook_lines),
        },
    }


def validate_vocadb_lyric_grounding_workspace(
    *,
    workspace_root: Path,
    output_root: Path,
) -> dict[str, Any]:
    workspace_root = workspace_root.resolve()
    output_root = output_root.resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    record_dirs = [
        workspace_root / "incoming",
        workspace_root / "accepted",
        workspace_root / "needs_patch",
    ]
    results: list[dict[str, Any]] = []
    for directory in record_dirs:
        for path in sorted(directory.glob("vocadb_*.json")):
            try:
                results.append(_validate_record(workspace_root, path))
            except Exception as exc:
                results.append(
                    {
                        "track_id": path.stem,
                        "record_path": str(path),
                        "grounding_status": "unknown",
                        "valid": False,
                        "issues": [f"validation_exception:{type(exc).__name__}"],
                        "counts": {"lyric_lines": 0, "sections": 0, "hook_lines": 0},
                    }
                )

    manifest = {
        "schema_version": "1.0",
        "record_type": "vocadb_lyric_grounding_validation_manifest",
        "workspace_root": str(workspace_root),
        "counts": {
            "records": len(results),
            "valid": sum(1 for item in results if item["valid"]),
            "invalid": sum(1 for item in results if not item["valid"]),
        },
        "results": results,
    }
    manifest_path = write_json(output_root / "vocadb_lyric_grounding_validation.json", manifest)
    manifest["manifest_path"] = str(manifest_path)
    return manifest
