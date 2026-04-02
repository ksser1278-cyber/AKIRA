from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .mode_support import load_json, write_json
from .reporting import write_utf8_json, write_utf8_text


TRACK_RECORD_KEYS = {
    "schema_version",
    "record_type",
    "track_identity",
    "source_provenance",
    "lyric_ground_truth",
    "song_intent",
    "audio_fact_layer",
    "section_analysis",
    "japanese_lyric_profile",
    "prompt_conditioning",
    "quality_control",
}


def _canonical_track_payload(payload: dict[str, Any]) -> dict[str, Any]:
    canonical = {key: payload[key] for key in TRACK_RECORD_KEYS if key in payload}
    canonical.setdefault("schema_version", "1.0")
    canonical["record_type"] = "track_conditioning_record"
    return canonical


def _track_target_path(project_root: Path, payload: dict[str, Any]) -> Path:
    track_identity = payload.get("track_identity", {})
    artist_id = str(track_identity.get("artist_id", "")).strip()
    track_id = str(track_identity.get("track_id", "")).strip()
    if not artist_id or not track_id:
        raise ValueError("mode support scaffold payload missing artist_id or track_id")
    prefix = f"{artist_id}_"
    stem = track_id[len(prefix):] if track_id.startswith(prefix) else track_id
    return project_root / "data" / artist_id / "reference_tracks" / f"{stem}.conditioning.json"


def materialize_mode_support_scaffolds(project_root: Path, mode_id: str, input_dir: Path) -> dict[str, Any]:
    mode_root = project_root / "data" / "_global" / "mode_support" / mode_id
    queue_path = mode_root / "queue.json"
    queue_payload = load_json(queue_path)
    queue = queue_payload.get("queue", [])
    created: list[dict[str, Any]] = []
    scaffolded_by_artist: set[str] = set()

    for path in sorted(input_dir.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if "track_identity" not in payload:
            continue
        canonical = _canonical_track_payload(payload)
        target_path = _track_target_path(project_root, canonical)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(json.dumps(canonical, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        artist_id = str(canonical.get("track_identity", {}).get("artist_id", "")).strip()
        track_id = str(canonical.get("track_identity", {}).get("track_id", "")).strip()
        if artist_id:
            scaffolded_by_artist.add(artist_id)
        created.append(
            {
                "artist_id": artist_id,
                "track_id": track_id,
                "source_path": str(path),
                "target_path": str(target_path),
            }
        )

    for item in queue:
        artist_id = str(item.get("artist_id", "")).strip()
        candidate_track_ids = [
            str(track_id).strip()
            for track_id in item.get("candidate_track_ids", [])
            if str(track_id).strip()
        ]
        if not candidate_track_ids:
            item["status"] = "artist_curation_pending"
        elif artist_id in scaffolded_by_artist:
            item["status"] = "scaffolded"
        else:
            item["status"] = "ready_for_scaffold"

    write_json(queue_path, queue_payload)

    return {
        "schema_version": "1.0",
        "mode_id": mode_id,
        "input_dir": str(input_dir),
        "queue_path": str(queue_path),
        "created_count": len(created),
        "created": created,
    }


def write_mode_support_scaffold_report(project_root: Path, payload: dict[str, Any]) -> tuple[Path, Path]:
    out_dir = project_root / "reports" / "quality" / "mode_support_scaffold"
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"{payload['mode_id']}_mode_support_scaffold.json"
    md_path = out_dir / f"{payload['mode_id']}_mode_support_scaffold.md"
    write_utf8_json(json_path, payload)
    lines = [
        f"# Mode Support Scaffold: {payload['mode_id']}",
        "",
        f"- Created conditioning files: `{payload['created_count']}`",
        f"- Queue: `{payload['queue_path']}`",
        "",
    ]
    for item in payload.get("created", []):
        lines.append(f"- `{item['artist_id']}` / `{item['track_id']}` / `{item['target_path']}`")
    write_utf8_text(md_path, "\n".join(lines), trailing_newline=False)
    return json_path, md_path
