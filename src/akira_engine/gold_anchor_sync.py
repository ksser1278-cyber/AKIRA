from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sync_gold_anchor_set(project_root: Path) -> dict[str, Any]:
    audit_dir = project_root / "reports" / "quality" / "conditioning"
    gold_anchor_path = project_root / "data" / "anchor_sets" / "gold_anchor_set.json"
    producer_expansion_path = project_root / "data" / "anchor_sets" / "producer_expansion_set.json"
    registry_path = project_root / "data" / "dataset_registry.json"

    gold_anchor = load_json(gold_anchor_path)
    producer_expansion = load_json(producer_expansion_path)
    registry = load_json(registry_path)

    promotion_results: list[dict[str, Any]] = []
    expansion_by_artist = {
        artist_block["artist_id"]: list(artist_block.get("track_ids", []))
        for artist_block in producer_expansion.get("artists", [])
    }

    synced_artists: list[dict[str, Any]] = []
    for artist_block in gold_anchor.get("artists", []):
        artist_id = artist_block["artist_id"]
        audit_path = audit_dir / f"{artist_id}_conditioning_audit_active.json"
        audit_payload = load_json(audit_path)
        gold_track_ids = [record["track_id"] for record in audit_payload.get("records", []) if record.get("grade") == "gold"]
        previous_track_ids = list(artist_block.get("track_ids", []))
        removed_track_ids = [track_id for track_id in previous_track_ids if track_id not in gold_track_ids]

        expansion_tracks = expansion_by_artist.setdefault(artist_id, [])
        for track_id in removed_track_ids:
            if track_id not in expansion_tracks:
                expansion_tracks.append(track_id)

        synced_artists.append(
            {
                "artist_id": artist_id,
                "track_ids": gold_track_ids,
            }
        )
        promotion_results.append(
            {
                "artist_id": artist_id,
                "gold_track_ids": gold_track_ids,
                "removed_track_ids": removed_track_ids,
                "audit_path": str(audit_path),
            }
        )

    gold_anchor["artists"] = synced_artists
    gold_anchor["notes"] = [
        "This set is synchronized from active conditioning audits.",
        "Only tracks graded gold should remain here.",
    ]

    producer_expansion["artists"] = [
        {
            "artist_id": artist_id,
            "track_ids": track_ids,
        }
        for artist_id, track_ids in expansion_by_artist.items()
    ]

    registry.setdefault("quality_rules", {})
    registry["quality_rules"]["gold_anchor_minimum_grade"] = "gold"
    registry["quality_rules"]["gold_target_grade"] = "gold"

    write_json(gold_anchor_path, gold_anchor)
    write_json(producer_expansion_path, producer_expansion)
    write_json(registry_path, registry)

    return {
        "gold_anchor_path": str(gold_anchor_path),
        "producer_expansion_path": str(producer_expansion_path),
        "dataset_registry_path": str(registry_path),
        "artists": promotion_results,
    }
