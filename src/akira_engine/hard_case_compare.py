from __future__ import annotations

from pathlib import Path
from typing import Any

from .manifest_tools import load_json
from .reporting import write_utf8_json, write_utf8_text


def _run_map(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(row.get("track_id", "")).strip(): row
        for row in manifest.get("runs", [])
        if str(row.get("track_id", "")).strip()
    }


def build_hard_case_comparison(
    *,
    baseline_manifest_path: Path,
    candidate_manifest_path: Path,
) -> dict[str, Any]:
    baseline = load_json(baseline_manifest_path)
    candidate = load_json(candidate_manifest_path)
    baseline_runs = _run_map(baseline)
    candidate_runs = _run_map(candidate)
    track_ids = sorted(set(baseline_runs) | set(candidate_runs))
    rows: list[dict[str, Any]] = []
    for track_id in track_ids:
        base_row = baseline_runs.get(track_id, {})
        cand_row = candidate_runs.get(track_id, {})
        baseline_score = float(base_row.get("selected_score", 0.0))
        candidate_score = float(cand_row.get("selected_score", 0.0))
        delta = round(candidate_score - baseline_score, 2)
        rows.append(
            {
                "track_id": track_id,
                "baseline_score": baseline_score,
                "candidate_score": candidate_score,
                "delta": delta,
                "baseline_candidate_id": str(base_row.get("selected_candidate_id", "")).strip(),
                "candidate_candidate_id": str(cand_row.get("selected_candidate_id", "")).strip(),
                "baseline_notes": [str(note).strip() for note in base_row.get("critic_notes", []) if str(note).strip()],
                "candidate_notes": [str(note).strip() for note in cand_row.get("critic_notes", []) if str(note).strip()],
            }
        )
    return {
        "schema_version": "1.0",
        "record_type": "hard_case_comparison",
        "artist_id": str(candidate.get("artist_id", baseline.get("artist_id", ""))).strip(),
        "baseline_manifest_path": str(baseline_manifest_path),
        "candidate_manifest_path": str(candidate_manifest_path),
        "baseline_average_score": float(baseline.get("average_score", 0.0)),
        "candidate_average_score": float(candidate.get("average_score", 0.0)),
        "average_delta": round(float(candidate.get("average_score", 0.0)) - float(baseline.get("average_score", 0.0)), 2),
        "tracks": rows,
    }


def render_hard_case_comparison_markdown(payload: dict[str, Any]) -> str:
    lines = [
        f"# {payload['artist_id']} Hard Case Comparison",
        "",
        f"- Baseline manifest: `{payload['baseline_manifest_path']}`",
        f"- Candidate manifest: `{payload['candidate_manifest_path']}`",
        f"- Baseline average: `{payload['baseline_average_score']}`",
        f"- Candidate average: `{payload['candidate_average_score']}`",
        f"- Average delta: `{payload['average_delta']}`",
        "",
    ]
    for row in payload.get("tracks", []):
        lines.extend(
            [
                f"## {row['track_id']}",
                f"- Baseline score: `{row['baseline_score']}`",
                f"- Candidate score: `{row['candidate_score']}`",
                f"- Delta: `{row['delta']}`",
                f"- Baseline candidate: `{row['baseline_candidate_id'] or 'none'}`",
                f"- Candidate candidate: `{row['candidate_candidate_id'] or 'none'}`",
                f"- Baseline notes: {'; '.join(row['baseline_notes']) if row['baseline_notes'] else 'none'}",
                f"- Candidate notes: {'; '.join(row['candidate_notes']) if row['candidate_notes'] else 'none'}",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def write_hard_case_comparison(
    *,
    baseline_manifest_path: Path,
    candidate_manifest_path: Path,
    output_dir: Path,
) -> dict[str, Any]:
    payload = build_hard_case_comparison(
        baseline_manifest_path=baseline_manifest_path,
        candidate_manifest_path=candidate_manifest_path,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = write_utf8_json(output_dir / "hard_case_comparison.json", payload)
    md_path = write_utf8_text(
        output_dir / "hard_case_comparison.md",
        render_hard_case_comparison_markdown(payload),
        trailing_newline=False,
    )
    payload["json_path"] = str(json_path)
    payload["markdown_path"] = str(md_path)
    return payload
