from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from .training_data import write_json


def _safe_text(value: Any) -> str:
    return str(value or "").strip()


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def materialize_lyric_technique_pilot_workspace(
    *,
    source_workspace_root: Path,
    pilot_manifest_path: Path,
    output_root: Path,
) -> dict[str, Any]:
    source_workspace_root = source_workspace_root.resolve()
    pilot_manifest_path = pilot_manifest_path.resolve()
    output_root = output_root.resolve()
    incoming_dir = output_root / "incoming"
    accepted_dir = output_root / "accepted"
    rejected_dir = output_root / "rejected"
    needs_patch_dir = output_root / "needs_patch"
    lyric_assets_dir = output_root / "lyric_assets"
    section_maps_dir = output_root / "section_maps"
    for directory in [incoming_dir, accepted_dir, rejected_dir, needs_patch_dir, lyric_assets_dir, section_maps_dir]:
        directory.mkdir(parents=True, exist_ok=True)

    manifest = _load_json(pilot_manifest_path)
    selected_tracks = manifest.get("selected_tracks", [])
    copied = 0
    skipped = 0
    for item in selected_tracks:
        track_id = _safe_text(item.get("track_id"))
        if not track_id:
            skipped += 1
            continue
        incoming_src = source_workspace_root / "incoming" / f"{track_id}.json"
        lyric_src = source_workspace_root / "lyric_assets" / f"{track_id}.txt"
        section_src = source_workspace_root / "section_maps" / f"{track_id}.sections.json"
        if not incoming_src.exists() or not lyric_src.exists() or not section_src.exists():
            skipped += 1
            continue
        shutil.copy2(incoming_src, incoming_dir / incoming_src.name)
        shutil.copy2(lyric_src, lyric_assets_dir / lyric_src.name)
        shutil.copy2(section_src, section_maps_dir / section_src.name)
        copied += 1

    readme = (
        "# Lyric Technique Pilot Workspace\n\n"
        "This is a reduced pilot subset copied from a larger vocadb lyric grounding workspace.\n\n"
        "Only the selected pilot tracks are included here.\n"
    )
    (output_root / "README.md").write_text(readme, encoding="utf-8")
    output_manifest = {
        "schema_version": "1.0",
        "record_type": "lyric_technique_pilot_workspace_manifest",
        "source_workspace_root": str(source_workspace_root),
        "pilot_manifest_path": str(pilot_manifest_path),
        "output_root": str(output_root),
        "counts": {
            "selected_tracks": len(selected_tracks),
            "copied_tracks": copied,
            "skipped_tracks": skipped,
        },
    }
    output_manifest_path = write_json(output_root / "workspace_manifest.json", output_manifest)
    output_manifest["manifest_path"] = str(output_manifest_path)
    return output_manifest
