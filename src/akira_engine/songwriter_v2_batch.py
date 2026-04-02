from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .lyric_draft import load_jsonl
from .lyric_draft_batch import select_diverse_records
from .songwriter_v2 import run_songwriter_v2


def write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def existing_track_ids(output_root: Path) -> set[str]:
    track_ids: set[str] = set()
    if not output_root.exists():
        return track_ids
    for plan_path in output_root.rglob("plan.json"):
        track_ids.add(plan_path.parent.name)
    return track_ids


def run_songwriter_v2_batch(
    source_jsonl: Path,
    *,
    count: int,
    output_root: Path,
    candidate_count: int,
    existing_output_root: Path | None = None,
) -> dict[str, Any]:
    records = load_jsonl(source_jsonl)
    if not records:
        raise ValueError(f"No records found in {source_jsonl}")

    exclude_track_ids = existing_track_ids(existing_output_root) if existing_output_root else set()
    selected = select_diverse_records(records, count=count, exclude_track_ids=exclude_track_ids)

    run_manifests: list[dict[str, Any]] = []
    for record in selected:
        artist_id = str(record.get("artist_id", "artist"))
        track_id = str(record.get("track_id", "track"))
        run_dir = output_root / artist_id / track_id
        run_manifests.append(
            run_songwriter_v2(
                source_jsonl,
                track_id=track_id,
                output_dir=run_dir,
                candidate_count=candidate_count,
            )
        )

    summary = {
        "count": len(run_manifests),
        "average_selected_score": round(
            sum(item["selected_score"] for item in run_manifests) / max(1, len(run_manifests)),
            2,
        ),
        "tracks_below_75": sum(1 for item in run_manifests if item["selected_score"] < 75),
        "tracks_75_to_85": sum(1 for item in run_manifests if 75 <= item["selected_score"] < 85),
        "tracks_85_plus": sum(1 for item in run_manifests if item["selected_score"] >= 85),
    }

    manifest = {
        "schema_version": "1.0",
        "source_jsonl": str(source_jsonl),
        "output_root": str(output_root),
        "candidate_count": candidate_count,
        "requested_count": count,
        "selected_track_ids": [record["track_id"] for record in selected],
        "summary": summary,
        "runs": [
            {
                "artist_id": item["artist_id"],
                "track_id": item["track_id"],
                "selected_candidate_id": item["selected_candidate_id"],
                "selected_score": item["selected_score"],
                "manifest_path": item["manifest_path"],
                "selected_lyric_path": item["selected_lyric_path"],
            }
            for item in run_manifests
        ],
    }
    manifest_path = write_json(output_root / "batch_manifest.json", manifest)
    manifest["manifest_path"] = str(manifest_path)
    return manifest


def render_songwriter_v2_batch_report(manifest: dict[str, Any]) -> str:
    summary = manifest["summary"]
    lines = [
        "# Songwriter V2 Batch Run",
        "",
        f"- Source JSONL: `{manifest['source_jsonl']}`",
        f"- Requested count: `{manifest['requested_count']}`",
        f"- Candidate count per track: `{manifest['candidate_count']}`",
        f"- Average selected score: `{summary['average_selected_score']}`",
        f"- Tracks below 75: `{summary['tracks_below_75']}`",
        f"- Tracks 75 to 85: `{summary['tracks_75_to_85']}`",
        f"- Tracks 85 plus: `{summary['tracks_85_plus']}`",
        "",
        "## Runs",
        "",
    ]
    for run in sorted(manifest["runs"], key=lambda item: item["selected_score"], reverse=True):
        lines.extend(
            [
                f"### {run['track_id']}",
                f"- Selected candidate: `{run['selected_candidate_id']}`",
                f"- Selected score: `{run['selected_score']}`",
                f"- Run manifest: `{run['manifest_path']}`",
                f"- Selected lyric: `{run['selected_lyric_path']}`",
                "",
            ]
        )
    return "\n".join(lines)
