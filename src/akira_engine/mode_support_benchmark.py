from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from .conditioning_brief_dataset import build_briefs_from_conditioning_paths
from .mode_support_audit import _candidate_paths_for_mode
from .reporting import write_utf8_json, write_utf8_text
from .songwriter_v2 import run_songwriter_v2


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _mode_lookup_for_paths(paths: list[Path], mode_id: str) -> list[tuple[Path, str]]:
    return [(path, mode_id) for path in paths]


def _brief_jsonl_for_mode(project_root: Path, mode_id: str, paths: list[Path]) -> Path:
    out_path = project_root / "datasets" / "experiments" / "_mode_support" / f"{mode_id}.jsonl"
    records = build_briefs_from_conditioning_paths(_mode_lookup_for_paths(paths, mode_id))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return out_path


def render_mode_support_benchmark_report(manifest: dict[str, Any]) -> str:
    lines = [
        f"# {manifest['mode_id']} Mode Support Benchmark",
        "",
        f"- Source JSONL: `{manifest['source_jsonl']}`",
        f"- Candidate count: `{manifest['candidate_count']}`",
        f"- Track count: `{manifest['track_count']}`",
        f"- Average score: `{manifest['average_score']}`",
        "",
    ]
    for run in sorted(manifest["runs"], key=lambda item: item["selected_score"], reverse=True):
        lines.extend(
            [
                f"## {run['track_id']}",
                f"- Artist: `{run['artist_id']}`",
                f"- Score: `{run['selected_score']}`",
                f"- Candidate: `{run['selected_candidate_id']}`",
                f"- Notes: {'; '.join(run['critic_notes']) if run['critic_notes'] else 'none'}",
                f"- Report: `{run['report_path']}`",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def run_mode_support_benchmark(
    *,
    project_root: Path,
    mode_id: str,
    output_root: Path,
    candidate_count: int,
) -> dict[str, Any]:
    paths = _candidate_paths_for_mode(project_root, mode_id)
    source_jsonl = _brief_jsonl_for_mode(project_root, mode_id, paths)
    runs: list[dict[str, Any]] = []
    for path in paths:
        payload = _load_json(path)
        identity = payload.get("track_identity", {})
        track_id = str(identity.get("track_id", "")).strip()
        artist_id = str(identity.get("artist_id", "")).strip()
        run_dir = output_root / mode_id / track_id
        run_manifest = run_songwriter_v2(
            source_jsonl,
            track_id=track_id,
            output_dir=run_dir,
            candidate_count=candidate_count,
            include_history=False,
        )
        critic_results = run_manifest.get("critic_results", [])
        winner = critic_results[0] if critic_results else {}
        runs.append(
            {
                "track_id": track_id,
                "artist_id": artist_id,
                "selected_score": run_manifest["selected_score"],
                "selected_candidate_id": run_manifest["selected_candidate_id"],
                "critic_notes": [str(note) for note in winner.get("critic_notes", []) if str(note).strip()],
                "report_path": str(run_dir / "run_report.md"),
                "manifest_path": run_manifest["manifest_path"],
            }
        )

    by_artist: dict[str, list[float]] = defaultdict(list)
    for run in runs:
        by_artist[run["artist_id"]].append(float(run["selected_score"]))

    manifest = {
        "schema_version": "1.0",
        "record_type": "mode_support_benchmark",
        "mode_id": mode_id,
        "source_jsonl": str(source_jsonl),
        "candidate_count": candidate_count,
        "track_count": len(runs),
        "average_score": round(sum(item["selected_score"] for item in runs) / max(1, len(runs)), 2),
        "artist_averages": {
            artist_id: round(sum(scores) / max(1, len(scores)), 2)
            for artist_id, scores in sorted(by_artist.items())
        },
        "runs": runs,
    }
    mode_output = output_root / mode_id
    manifest_path = write_utf8_json(mode_output / "mode_support_benchmark_manifest.json", manifest)
    report_path = write_utf8_text(
        mode_output / "mode_support_benchmark_report.md",
        render_mode_support_benchmark_report(manifest),
        trailing_newline=False,
    )
    manifest["manifest_path"] = str(manifest_path)
    manifest["report_path"] = str(report_path)
    return manifest
