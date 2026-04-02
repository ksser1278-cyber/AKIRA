from __future__ import annotations

from pathlib import Path
from typing import Any

from .manifest_tools import load_json


def build_baseline_status(project_root: Path) -> dict[str, Any]:
    health = load_json(project_root / "reports" / "health" / "engine_health.json")
    benchmark_registry = load_json(project_root / "data" / "benchmark_registry.json")
    hard_case_registry = load_json(project_root / "data" / "_global" / "hard_case_registry.json")

    approved_benchmarks: list[dict[str, Any]] = []
    for artist in benchmark_registry.get("artists", []):
        approved_benchmarks.append(
            {
                "artist_id": str(artist.get("artist_id", "")).strip(),
                "approved_manifest_path": str(artist.get("approved_manifest_path", "")).strip(),
                "notes": [str(note).strip() for note in artist.get("notes", []) if str(note).strip()],
            }
        )

    hard_case_summary: list[dict[str, Any]] = []
    for artist in hard_case_registry.get("artists", []):
        tracks = artist.get("tracks", [])
        hard_case_summary.append(
            {
                "artist_id": str(artist.get("artist_id", "")).strip(),
                "benchmark_manifest_path": str(artist.get("benchmark_manifest_path", "")).strip(),
                "benchmark_average_score": float(artist.get("benchmark_average_score", 0.0)),
                "open_tracks": [
                    str(track.get("track_id", "")).strip()
                    for track in tracks
                    if str(track.get("status", "")).strip() == "open" and str(track.get("track_id", "")).strip()
                ],
                "resolved_tracks": [
                    str(track.get("track_id", "")).strip()
                    for track in tracks
                    if str(track.get("status", "")).strip() == "resolved" and str(track.get("track_id", "")).strip()
                ],
                "deferred_tracks": [
                    {
                        "track_id": str(track.get("track_id", "")).strip(),
                        "reason": str(track.get("deferred_reason", "")).strip(),
                    }
                    for track in tracks
                    if str(track.get("status", "")).strip() == "deferred" and str(track.get("track_id", "")).strip()
                ],
            }
        )

    return {
        "schema_version": "1.0",
        "record_type": "baseline_status",
        "snapshot_date": "2026-03-22",
        "approved_anchor_benchmarks": approved_benchmarks,
        "artists": health.get("artists", []),
        "mode_support": health.get("mode_support", {}),
        "hard_case": hard_case_summary,
    }


def render_baseline_status_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Pinned Baseline Snapshot",
        "",
        f"- Snapshot date: `{payload.get('snapshot_date', '')}`",
        "- This file is a pinned benchmark snapshot. Use `reports/health/engine_health.md` and `reports/planning/execution_backlog.md` for current live operations.",
        "",
        "## Approved Anchor Benchmarks",
        "",
    ]

    for artist in payload.get("approved_anchor_benchmarks", []):
        note_text = "; ".join(artist.get("notes", [])) or "none"
        lines.append(
            f"- `{artist['artist_id']}` / `{artist['approved_manifest_path']}` / {note_text}"
        )

    lines.extend([
        "",
        "## Anchors",
        "",
    ])

    for artist in payload.get("artists", []):
        lines.extend(
            [
                f"### {artist['artist_id']}",
                f"- Conditioning: `{artist['conditioning']['average_score']}` avg / gold `{artist['conditioning']['gold_count']}` / usable `{artist['conditioning']['usable_count']}` / weak `{artist['conditioning']['weak_count']}`",
                f"- Producer expansion: `{artist['producer_expansion']['average_score']}` avg / gold `{artist['producer_expansion']['gold_count']}` / usable `{artist['producer_expansion']['usable_count']}` / weak `{artist['producer_expansion']['weak_count']}`",
                f"- Benchmark: `{artist['benchmark']['average_score']}` avg across `{artist['benchmark']['track_count']}` tracks",
                f"- Approved manifest: `{artist['benchmark_manifest_path']}`",
                "",
            ]
        )

    mode_support = payload.get("mode_support", {})
    lines.extend(
        [
            "## Mode Support",
            "",
            f"- Modes: `{mode_support.get('mode_count', 0)}`",
            f"- Scaffolded artists: `{mode_support.get('scaffolded_artist_count', 0)}`",
            f"- Ready artists: `{mode_support.get('ready_artist_count', 0)}`",
            "",
        ]
    )
    for benchmark in mode_support.get("benchmarks", []):
        weakest_summary = ", ".join(
            f"{item['track_id']}:{item['score']}"
            for item in benchmark.get("weakest_tracks", [])
        ) or "none"
        lines.append(
            f"- `{benchmark['mode_id']}` / avg `{benchmark['average_score']}` / weakest {weakest_summary}"
        )
    lines.append("")

    lines.extend(["## Hard Case", ""])
    for artist in payload.get("hard_case", []):
        lines.append(f"### {artist['artist_id']}")
        lines.append(f"- Benchmark: `{artist['benchmark_average_score']}` / `{artist['benchmark_manifest_path']}`")
        lines.append(f"- Open: `{', '.join(artist.get('open_tracks', [])) or 'none'}`")
        lines.append(f"- Resolved: `{', '.join(artist.get('resolved_tracks', [])) or 'none'}`")
        deferred = artist.get("deferred_tracks", [])
        if deferred:
            deferred_summary = ", ".join(
                f"{item['track_id']} ({item['reason']})"
                for item in deferred
            )
            lines.append(
                "- Deferred: " + deferred_summary
            )
        else:
            lines.append("- Deferred: `none`")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"
