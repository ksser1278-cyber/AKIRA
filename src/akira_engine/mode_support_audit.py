from __future__ import annotations

from pathlib import Path
from typing import Any

from .conditioning_audit import audit_conditioning_paths, render_audit_markdown
from .manifest_tools import load_json
from .reporting import write_utf8_json, write_utf8_text


def _candidate_paths_for_mode(project_root: Path, mode_id: str) -> list[Path]:
    queue_path = project_root / "data" / "_global" / "mode_support" / mode_id / "queue.json"
    queue_payload = load_json(queue_path)
    paths: list[Path] = []
    seen: set[Path] = set()
    for item in queue_payload.get("queue", []):
        candidate_track_ids = [
            str(track_id).strip()
            for track_id in item.get("candidate_track_ids", [])
            if str(track_id).strip()
        ]
        for track_id in candidate_track_ids:
            artist_id, _, stem = track_id.partition("_")
            if not artist_id or not stem:
                continue
            path = project_root / "data" / artist_id / "reference_tracks" / f"{stem}.conditioning.json"
            if path.exists() and path not in seen:
                seen.add(path)
                paths.append(path)
    return paths


def build_mode_support_audit(project_root: Path, mode_id: str) -> dict[str, Any]:
    paths = _candidate_paths_for_mode(project_root, mode_id)
    summary = audit_conditioning_paths(paths, mode_id)
    summary["record_type"] = "mode_support_audit"
    summary["mode_id"] = mode_id
    return summary


def write_mode_support_audit(project_root: Path, mode_id: str, summary: dict[str, Any]) -> tuple[Path, Path]:
    output_dir = project_root / "reports" / "quality" / "mode_support_audit"
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / f"{mode_id}_mode_support_audit.json"
    md_path = output_dir / f"{mode_id}_mode_support_audit.md"
    write_utf8_json(json_path, summary)
    write_utf8_text(md_path, render_audit_markdown(summary), trailing_newline=False)
    return json_path, md_path
