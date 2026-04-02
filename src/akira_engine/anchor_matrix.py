from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

from .manifest_tools import load_json
from .reporting import write_utf8_json, write_utf8_text
from .songwriter_v2 import run_songwriter_v2


def normalize_lookup_text(value: Any) -> str:
    text = str(value or "").strip().lower()
    return "".join(char for char in text if char.isalnum() or "\u3040" <= char <= "\u9fff" or char == "ー")


def build_mode_lookup(generated_profile: dict[str, Any]) -> dict[str, str]:
    lookup: dict[str, str] = {}
    for item in generated_profile.get("generated_from_conditioning", {}).get("track_mode_assignments", []):
        mode_id = str(item.get("mode_id", "")).strip()
        if not mode_id:
            continue
        for key in [item.get("track_id"), item.get("title_core"), item.get("title")]:
            normalized = normalize_lookup_text(key)
            if normalized:
                lookup[normalized] = mode_id
    return lookup


def load_anchor_specs(artist_id: str, project_root: Path) -> list[dict[str, str]]:
    generated_profile_path = project_root / "artists" / artist_id / "style_prompt_profile.generated.json"
    mode_lookup: dict[str, str] = {}
    if generated_profile_path.exists():
        generated_profile = load_json(generated_profile_path)
        mode_lookup = build_mode_lookup(generated_profile)

    reference_dir = project_root / "data" / artist_id / "reference_tracks"
    queue_path = reference_dir / "conditioning_queue.json"
    queue_mode_lookup: dict[str, str] = {}
    active_track_ids: set[str] | None = None
    if queue_path.exists():
        queue = load_json(queue_path)
        active_track_ids = set()
        for item in queue.get("queue", []):
            status = str(item.get("status", "")).strip().lower()
            if status == "pending":
                continue
            track_id = str(item.get("track_id", "")).strip()
            if not track_id:
                continue
            active_track_ids.add(track_id)
            mode_id = str(item.get("mode", "")).strip()
            if mode_id:
                queue_mode_lookup[track_id] = mode_id

    anchors: list[dict[str, str]] = []
    for path in sorted(reference_dir.glob("*.conditioning.json")):
        payload = load_json(path)
        identity = payload.get("track_identity", {})
        anchor_track_id = str(identity.get("track_id", "")).strip()
        if active_track_ids is not None and anchor_track_id not in active_track_ids:
            continue
        source_track_id = anchor_track_id

        mode_id = queue_mode_lookup.get(anchor_track_id, "")
        for key in [identity.get("track_id"), identity.get("title_core"), identity.get("title"), source_track_id]:
            normalized = normalize_lookup_text(key)
            if normalized and normalized in mode_lookup:
                mode_id = mode_lookup[normalized]
                break

        anchors.append(
            {
                "conditioning_file": str(path),
                "source_track_id": source_track_id,
                "anchor_track_id": anchor_track_id,
                "title": str(identity.get("title_core") or identity.get("title") or source_track_id).strip(),
                "mode_id": mode_id or "unknown",
            }
        )
    return anchors


def summarize_notes(critic_results: list[dict[str, Any]]) -> list[str]:
    winner = critic_results[0] if critic_results else {}
    return [str(note) for note in winner.get("critic_notes", []) if str(note).strip()]


def render_anchor_matrix_report(manifest: dict[str, Any]) -> str:
    lines = [
        f"# {manifest['artist_id']} Anchor Matrix",
        "",
        f"- Source JSONL: `{manifest['source_jsonl']}`",
        f"- Candidate count: `{manifest['candidate_count']}`",
        f"- Anchor count: `{manifest['anchor_count']}`",
        f"- Average score: `{manifest['summary']['average_score']}`",
        "",
        "## Mode Averages",
        "",
    ]

    for mode_id, stats in manifest["summary"]["mode_averages"].items():
        lines.append(f"- `{mode_id}`: average `{stats['average_score']}` across `{stats['count']}` tracks")

    lines.extend(["", "## Track Scores", ""])
    for run in sorted(manifest["runs"], key=lambda item: item["selected_score"]):
        lines.extend(
            [
                f"### {run['title']}",
                f"- Track id: `{run['source_track_id']}`",
                f"- Mode: `{run['mode_id']}`",
                f"- Score: `{run['selected_score']}`",
                f"- Candidate: `{run['selected_candidate_id']}`",
                f"- Notes: {'; '.join(run['critic_notes']) if run['critic_notes'] else 'none'}",
                f"- Selected lyric: `{run['selected_lyric_path']}`",
                f"- Report: `{run['report_path']}`",
                "",
            ]
        )

    weakest = manifest["summary"]["weakest_tracks"]
    if weakest:
        lines.extend(["## Weakest Tracks", ""])
        for item in weakest:
            lines.append(
                f"- `{item['source_track_id']}` / `{item['mode_id']}` / `{item['selected_score']}` / {'; '.join(item['critic_notes']) if item['critic_notes'] else 'none'}"
            )
        lines.append("")

    return "\n".join(lines)


def run_anchor_matrix(
    *,
    artist_id: str,
    source_jsonl: Path,
    output_root: Path,
    candidate_count: int,
    project_root: Path,
) -> dict[str, Any]:
    anchors = load_anchor_specs(artist_id, project_root)
    artist_output_root = output_root
    if artist_output_root.name != artist_id:
        artist_output_root = artist_output_root / artist_id

    runs: list[dict[str, Any]] = []
    for anchor in anchors:
        run_dir = artist_output_root / anchor["source_track_id"]
        run_manifest = run_songwriter_v2(
            source_jsonl,
            track_id=anchor["source_track_id"],
            output_dir=run_dir,
            candidate_count=candidate_count,
            include_history=True,
        )
        critic_notes = summarize_notes(run_manifest.get("critic_results", []))
        runs.append(
            {
                "title": anchor["title"],
                "mode_id": anchor["mode_id"],
                "source_track_id": anchor["source_track_id"],
                "anchor_track_id": anchor["anchor_track_id"],
                "conditioning_file": anchor["conditioning_file"],
                "selected_score": run_manifest["selected_score"],
                "selected_candidate_id": run_manifest["selected_candidate_id"],
                "selected_lyric_path": run_manifest["selected_lyric_path"],
                "report_path": str(run_dir / "run_report.md"),
                "manifest_path": run_manifest["manifest_path"],
                "critic_notes": critic_notes,
            }
        )

    mode_buckets: dict[str, list[float]] = defaultdict(list)
    for run in runs:
        mode_buckets[run["mode_id"]].append(float(run["selected_score"]))

    mode_averages = {
        mode_id: {
            "count": len(scores),
            "average_score": round(sum(scores) / max(1, len(scores)), 2),
        }
        for mode_id, scores in sorted(mode_buckets.items())
    }

    summary = {
        "average_score": round(sum(run["selected_score"] for run in runs) / max(1, len(runs)), 2),
        "mode_averages": mode_averages,
        "weakest_tracks": sorted(runs, key=lambda item: item["selected_score"])[:5],
    }

    manifest = {
        "schema_version": "1.0",
        "artist_id": artist_id,
        "source_jsonl": str(source_jsonl),
        "candidate_count": candidate_count,
        "anchor_count": len(runs),
        "summary": summary,
        "runs": runs,
    }

    manifest_path = write_utf8_json(artist_output_root / "anchor_matrix_manifest.json", manifest)
    report_path = write_utf8_text(
        artist_output_root / "anchor_matrix_report.md",
        render_anchor_matrix_report(manifest),
        trailing_newline=False,
    )
    manifest["manifest_path"] = str(manifest_path)
    manifest["report_path"] = str(report_path)
    return manifest
