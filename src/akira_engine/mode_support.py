from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_mode_support_queue(project_root: Path, mode_block: dict[str, Any]) -> dict[str, Any]:
    mode_id = str(mode_block.get("mode_id", "")).strip()
    target_count = int(mode_block.get("target_count", 0) or 0)
    support_artists = [str(artist_id).strip() for artist_id in mode_block.get("support_artists", []) if str(artist_id).strip()]

    queue: list[dict[str, Any]] = []
    for artist_id in support_artists:
        queue.append(
            {
                "artist_id": artist_id,
                "status": "artist_curation_pending",
                "target_track_count": max(1, target_count // max(len(support_artists), 1)),
                "candidate_track_ids": [],
                "notes": [
                    "Curate support tracks for this artist before creating conditioning scaffolds.",
                    "Keep entries mode-aligned and avoid duplicating current gold anchors.",
                ],
            }
        )

    return {
        "schema_version": "1.0",
        "record_type": "mode_support_queue",
        "mode_id": mode_id,
        "target_count": target_count,
        "support_artists": support_artists,
        "queue": queue,
    }


def scaffold_mode_support(project_root: Path) -> list[str]:
    manifest = load_json(project_root / "data" / "anchor_sets" / "mode_support_set.json")
    output_root = project_root / "data" / "_global" / "mode_support"
    created: list[str] = []

    for mode_block in manifest.get("modes", []):
        mode_id = str(mode_block.get("mode_id", "")).strip()
        if not mode_id:
            continue
        mode_dir = output_root / mode_id
        queue_path = mode_dir / "queue.json"
        if not queue_path.exists():
            write_json(queue_path, build_mode_support_queue(project_root, mode_block))
            created.append(str(queue_path))

        handoff_dir = mode_dir / "external_handoff" / "incoming"
        handoff_dir.mkdir(parents=True, exist_ok=True)

    return created
