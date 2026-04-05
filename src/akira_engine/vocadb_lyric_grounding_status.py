from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .training_data import write_json


def _safe_text(value: Any) -> str:
    return str(value or "").strip()


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _count_records(directory: Path) -> int:
    if not directory.exists():
        return 0
    return len(list(directory.glob("vocadb_*.json")))


def report_vocadb_lyric_grounding_status(
    *,
    workspaces_root: Path,
    output_root: Path,
) -> dict[str, Any]:
    workspaces_root = workspaces_root.resolve()
    output_root = output_root.resolve()
    output_root.mkdir(parents=True, exist_ok=True)

    workspace_rows: list[dict[str, Any]] = []
    for workspace in sorted(path for path in workspaces_root.iterdir() if path.is_dir()):
        manifest_path = workspace / "workspace_manifest.json"
        manifest = _load_json(manifest_path) if manifest_path.exists() else {}
        workspace_rows.append(
            {
                "workspace_name": workspace.name,
                "workspace_root": str(workspace),
                "selected_tracks": int(manifest.get("counts", {}).get("selected_tracks", 0) or 0),
                "copied_tracks": int(manifest.get("counts", {}).get("copied_tracks", 0) or 0),
                "incoming": _count_records(workspace / "incoming"),
                "accepted": _count_records(workspace / "accepted"),
                "needs_patch": _count_records(workspace / "needs_patch"),
                "rejected": _count_records(workspace / "rejected"),
                "lyric_assets": len(list((workspace / "lyric_assets").glob("vocadb_*.txt"))) if (workspace / "lyric_assets").exists() else 0,
                "section_maps": len(list((workspace / "section_maps").glob("vocadb_*.sections.json"))) if (workspace / "section_maps").exists() else 0,
            }
        )

    workspace_rows.sort(key=lambda item: (-item["accepted"], -item["incoming"], item["workspace_name"]))
    manifest = {
        "schema_version": "1.0",
        "record_type": "vocadb_lyric_grounding_status_report",
        "workspaces_root": str(workspaces_root),
        "counts": {
            "workspaces": len(workspace_rows),
            "total_incoming": sum(item["incoming"] for item in workspace_rows),
            "total_accepted": sum(item["accepted"] for item in workspace_rows),
            "total_needs_patch": sum(item["needs_patch"] for item in workspace_rows),
            "total_rejected": sum(item["rejected"] for item in workspace_rows),
        },
        "workspaces": workspace_rows,
    }
    manifest_path = write_json(output_root / "vocadb_lyric_grounding_status.json", manifest)
    manifest["manifest_path"] = str(manifest_path)
    return manifest
