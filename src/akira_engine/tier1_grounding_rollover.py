from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .lyric_technique_pilot_batch import build_lyric_technique_pilot_batch
from .lyric_technique_pilot_workspace import materialize_lyric_technique_pilot_workspace
from .training_data import write_json


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _workspace_track_ids(workspace: Path) -> set[str]:
    ids: set[str] = set()
    for bucket in ("incoming", "accepted", "needs_patch", "rejected"):
        directory = workspace / bucket
        if not directory.exists():
            continue
        for path in directory.glob("vocadb_*.json"):
            ids.add(path.stem)
    return ids


def _count_records(directory: Path) -> int:
    if not directory.exists():
        return 0
    return len(list(directory.glob("vocadb_*.json")))


def _workspace_is_closed(workspace: Path) -> bool:
    return _count_records(workspace / "incoming") == 0


def _next_workspace_name(workspaces_root: Path, prefix: str) -> str:
    existing = {path.name for path in workspaces_root.iterdir() if path.is_dir()}
    index = 1
    while True:
        candidate = f"{prefix}_v{index}"
        if candidate not in existing:
            return candidate
        index += 1


def advance_tier1_grounding_lane(
    *,
    queue_root: Path,
    source_workspace_root: Path,
    workspaces_root: Path,
    planning_root: Path,
    current_workspace_root: Path,
    batch_size: int = 10,
    workspace_name_prefix: str = "tier1_map_seed_pilot_auto",
) -> dict[str, Any]:
    queue_root = queue_root.resolve()
    source_workspace_root = source_workspace_root.resolve()
    workspaces_root = workspaces_root.resolve()
    planning_root = planning_root.resolve()
    current_workspace_root = current_workspace_root.resolve()
    planning_root.mkdir(parents=True, exist_ok=True)
    workspaces_root.mkdir(parents=True, exist_ok=True)

    processed_ids: set[str] = set()
    for workspace in sorted(path for path in workspaces_root.iterdir() if path.is_dir()):
        processed_ids.update(_workspace_track_ids(workspace))

    closed_current = _workspace_is_closed(current_workspace_root)
    next_workspace_manifest = None
    next_batch_manifest = None
    selected_count = 0
    next_workspace_root = None

    if closed_current:
        next_name = _next_workspace_name(workspaces_root, workspace_name_prefix)
        batch_output_root = planning_root / next_name
        next_batch_manifest = build_lyric_technique_pilot_batch(
            queue_root=queue_root,
            output_root=batch_output_root,
            batch_size=batch_size,
            exclude_track_ids=sorted(processed_ids),
        )
        if next_batch_manifest["counts"]["selected"] > 0:
            next_workspace_root = workspaces_root / next_name
            next_workspace_manifest = materialize_lyric_technique_pilot_workspace(
                source_workspace_root=source_workspace_root,
                pilot_manifest_path=Path(next_batch_manifest["manifest_path"]),
                output_root=next_workspace_root,
            )
            selected_count = next_workspace_manifest["counts"]["copied_tracks"]

    manifest = {
        "schema_version": "1.0",
        "record_type": "tier1_grounding_rollover_manifest",
        "queue_root": str(queue_root),
        "source_workspace_root": str(source_workspace_root),
        "workspaces_root": str(workspaces_root),
        "current_workspace_root": str(current_workspace_root),
        "counts": {
            "processed_track_ids": len(processed_ids),
            "closed_current": 1 if closed_current else 0,
            "selected_next_tracks": selected_count,
        },
        "outputs": {
            "next_batch_manifest": next_batch_manifest["manifest_path"] if next_batch_manifest else "",
            "next_workspace_manifest": next_workspace_manifest["manifest_path"] if next_workspace_manifest else "",
            "next_workspace_root": str(next_workspace_root) if next_workspace_root else "",
        },
    }
    manifest_path = write_json(planning_root / "tier1_grounding_rollover_manifest.json", manifest)
    manifest["manifest_path"] = str(manifest_path)
    return manifest
