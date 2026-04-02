from __future__ import annotations

from pathlib import Path
from typing import Any

from .manifest_tools import load_json
from .reporting import write_utf8_json, write_utf8_text
from .songwriter_v2 import run_songwriter_v2


def load_hard_case_track_ids(project_root: Path, artist_id: str) -> list[str]:
    registry = load_json(project_root / "data" / "_global" / "hard_case_registry.json")
    for artist in registry.get("artists", []):
        if str(artist.get("artist_id", "")).strip() != artist_id:
            continue
        return [
            str(item.get("track_id", "")).strip()
            for item in artist.get("tracks", [])
            if str(item.get("track_id", "")).strip()
        ]
    return []


def render_report(manifest: dict[str, Any]) -> str:
    lines = [
        f"# {manifest['artist_id']} Hard Case Benchmark",
        "",
        f"- Source JSONL: `{manifest['source_jsonl']}`",
        f"- Candidate count: `{manifest['candidate_count']}`",
        f"- Track count: `{manifest['track_count']}`",
        f"- Average score: `{manifest['average_score']}`",
        f"- Best current average: `{manifest.get('current_average_score', 0.0)}`",
        "",
    ]
    for row in manifest.get("runs", []):
        lines.extend(
            [
                f"## {row['track_id']}",
                f"- Score: `{row['selected_score']}`",
                f"- Candidate: `{row['selected_candidate_id']}`",
                f"- Best current score: `{row.get('current_best_score', 0.0)}`",
                f"- Best current candidate: `{row.get('current_best_candidate_id', '') or 'none'}`",
                f"- Notes: {'; '.join(row['critic_notes']) if row['critic_notes'] else 'none'}",
                f"- Report: `{row['report_path']}`",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def run_hard_case_benchmark(
    *,
    project_root: Path,
    artist_id: str,
    source_jsonl: Path,
    output_root: Path,
    candidate_count: int,
) -> dict[str, Any]:
    track_ids = load_hard_case_track_ids(project_root, artist_id)
    runs: list[dict[str, Any]] = []
    artist_output_root = output_root / artist_id
    artist_output_root.mkdir(parents=True, exist_ok=True)

    for track_id in track_ids:
        run_dir = artist_output_root / track_id
        result = run_songwriter_v2(
            source_jsonl,
            track_id=track_id,
            output_dir=run_dir,
            candidate_count=candidate_count,
            include_history=True,
        )
        critic_rows = result.get("critic_results", [])
        winner = critic_rows[0] if critic_rows else {}
        current_rows = [
            row for row in critic_rows
            if "-candidate-" in str(row.get("candidate_id", ""))
        ]
        current_best = current_rows[0] if current_rows else {}
        runs.append(
            {
                "track_id": track_id,
                "selected_score": float(result.get("selected_score", 0.0)),
                "selected_candidate_id": str(result.get("selected_candidate_id", "")).strip(),
                "current_best_score": float(
                    current_best.get("total_score", current_best.get("scores", {}).get("total", 0.0))
                ),
                "current_best_candidate_id": str(current_best.get("candidate_id", "")).strip(),
                "current_best_notes": [str(note).strip() for note in current_best.get("critic_notes", []) if str(note).strip()],
                "critic_notes": [str(note).strip() for note in winner.get("critic_notes", []) if str(note).strip()],
                "report_path": str(run_dir / "run_report.md"),
                "selected_lyric_path": str(result.get("selected_lyric_path", "")),
            }
        )

    average_score = round(sum(item["selected_score"] for item in runs) / max(1, len(runs)), 2)
    current_average_score = round(sum(item["current_best_score"] for item in runs) / max(1, len(runs)), 2)
    manifest = {
        "schema_version": "1.0",
        "record_type": "hard_case_benchmark",
        "artist_id": artist_id,
        "source_jsonl": str(source_jsonl),
        "candidate_count": candidate_count,
        "track_count": len(runs),
        "average_score": average_score,
        "current_average_score": current_average_score,
        "runs": runs,
    }
    manifest_path = write_utf8_json(artist_output_root / "hard_case_manifest.json", manifest)
    report_path = write_utf8_text(artist_output_root / "hard_case_report.md", render_report(manifest), trailing_newline=False)
    manifest["manifest_path"] = str(manifest_path)
    manifest["report_path"] = str(report_path)
    return manifest
