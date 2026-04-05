from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .manifest_tools import latest_benchmark_manifest


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def audio_index(project_root_path: Path | None = None) -> dict[str, dict[str, Any]]:
    root = project_root_path or project_root()
    summary_path = root / "reports" / "audio" / "audio_analysis_summary.json"
    if not summary_path.exists():
        return {}
    payload = load_json(summary_path)
    return {
        str(track.get("track_id", "")).strip(): track
        for track in payload.get("tracks", [])
        if str(track.get("track_id", "")).strip()
    }


def conditioning_audit_payload(artist_id: str, project_root_path: Path | None = None) -> dict[str, Any] | None:
    root = project_root_path or project_root()
    report_path = (
        root
        / "reports"
        / "quality"
        / "conditioning"
        / f"{artist_id}_conditioning_audit_active.json"
    )
    if not report_path.exists():
        return None
    return load_json(report_path)


def producer_expansion_audit_payload(artist_id: str, project_root_path: Path | None = None) -> dict[str, Any] | None:
    root = project_root_path or project_root()
    report_path = (
        root
        / "reports"
        / "quality"
        / "conditioning"
        / f"{artist_id}_producer_expansion_audit.json"
    )
    if not report_path.exists():
        return None
    return load_json(report_path)


def build_artist_health(
    artist_id: str,
    audio_tracks: dict[str, dict[str, Any]],
    generation_safety_by_artist: dict[str, dict[str, Any]],
    *,
    project_root_path: Path | None = None,
) -> dict[str, Any]:
    root = project_root_path or project_root()
    benchmark_path = latest_benchmark_manifest(root, artist_id)
    benchmark = load_json(benchmark_path) if benchmark_path else {}
    audit = conditioning_audit_payload(artist_id, root) or {}
    expansion_audit = producer_expansion_audit_payload(artist_id, root) or {}
    demo_smoke = demo_smoke_payload(artist_id, root)
    runs = benchmark.get("runs", [])
    if not runs and benchmark.get("rows"):
        runs = [
            {
                "source_track_id": row.get("track_id"),
                "selected_score": row.get("score"),
                "critic_notes": [],
            }
            for row in benchmark.get("rows", [])
        ]
    weakest = benchmark.get("summary", {}).get("weakest_tracks", [])
    if not weakest and benchmark.get("rows"):
        weakest = sorted(
            [
                {
                    "source_track_id": row.get("track_id"),
                    "selected_score": row.get("score"),
                    "critic_notes": [],
                }
                for row in benchmark.get("rows", [])
            ],
            key=lambda item: float(item.get("selected_score", 0.0)),
        )[:3]
    benchmark_average = float(
        benchmark.get("summary", {}).get("average_score", benchmark.get("mean_score", 0.0))
    )
    if not benchmark_average and runs:
        benchmark_average = round(
            sum(float(run.get("selected_score", 0.0)) for run in runs) / len(runs),
            3,
        )
    tracked_ids = [str(run.get("source_track_id", "")).strip() for run in runs]
    audio_coverage = [track_id for track_id in tracked_ids if track_id in audio_tracks]

    blockers: list[str] = []
    if audit:
        if int(audit.get("weak_count", 0)) > 0:
            blockers.append("conditioning quality still has weak records")
        if float(audit.get("average_score", 0.0)) < 80:
            blockers.append("conditioning audit average is below 80")
    else:
        blockers.append("conditioning audit is missing")

    if benchmark:
        if benchmark_average < 90:
            blockers.append("benchmark average is below 90")
        for item in weakest[:3]:
            notes = [str(note) for note in item.get("critic_notes", [])]
            if any("template-heavy" in note for note in notes):
                blockers.append("phrasing still feels template-heavy")
                break
    else:
        blockers.append("benchmark manifest is missing")

    if tracked_ids and len(audio_coverage) < len(tracked_ids):
        blockers.append("audio coverage is incomplete for active benchmark")

    if expansion_audit:
        if int(expansion_audit.get("weak_count", 0)) > 0:
            blockers.append("producer expansion still has weak records")
        if float(expansion_audit.get("average_score", 0.0)) < 70:
            blockers.append("producer expansion audit average is below 70")

    if not demo_smoke.get("latest_runs"):
        blockers.append("demo smoke coverage is missing")
    else:
        if any(float(run.get("selected_demo_adjusted_score", 0.0)) < 85 for run in demo_smoke.get("latest_runs", [])):
            blockers.append("demo smoke adjusted score is below 85")
        if any(float(run.get("release_score", 0.0)) < 0.8 for run in demo_smoke.get("latest_runs", [])):
            blockers.append("final chorus release is still weak in demo smoke")
        if any(float(run.get("imagery_specificity_score", 0.0)) < 0.7 for run in demo_smoke.get("latest_runs", [])):
            blockers.append("surface imagery is still too abstract in demo smoke")
        if any(
            str(run.get("generation_mode", "")).strip() == "template"
            and str(run.get("requested_generation_mode", "")).strip() != "template"
            for run in demo_smoke.get("latest_runs", [])
        ):
            blockers.append("demo smoke is still running in template mode")

    generation_safety = generation_safety_by_artist.get(
        artist_id,
        {
            "record_count": 0,
            "invalid_count": 0,
            "audit_only_count": 0,
            "planner_safe_count": 0,
            "generation_safe_count": 0,
            "benchmark_safe_count": 0,
        },
    )
    generation_safety_alerts: list[str] = []
    if generation_safety.get("record_count", 0) > 0 and generation_safety.get("planner_safe_count", 0) == 0:
        generation_safety_alerts.append("no planner-safe generation records in pilot relabel")
    if generation_safety.get("audit_only_count", 0) > 0:
        generation_safety_alerts.append("generation pilot still shows audit-only records")
    if generation_safety.get("invalid_count", 0) > 0:
        generation_safety_alerts.append("generation pilot still shows invalid records")

    return {
        "artist_id": artist_id,
        "conditioning_audit_path": str(
            root
            / "reports"
            / "quality"
            / "conditioning"
            / f"{artist_id}_conditioning_audit_active.json"
        )
        if audit
        else "",
        "benchmark_manifest_path": str(benchmark_path) if benchmark_path else "",
        "conditioning": {
            "record_count": int(audit.get("record_count", 0)),
            "gold_count": int(audit.get("gold_count", 0)),
            "usable_count": int(audit.get("usable_count", 0)),
            "weak_count": int(audit.get("weak_count", 0)),
            "average_score": float(audit.get("average_score", 0.0)),
        },
        "producer_expansion": {
            "record_count": int(expansion_audit.get("record_count", 0)),
            "gold_count": int(expansion_audit.get("gold_count", 0)),
            "usable_count": int(expansion_audit.get("usable_count", 0)),
            "weak_count": int(expansion_audit.get("weak_count", 0)),
            "average_score": float(expansion_audit.get("average_score", 0.0)),
        },
        "benchmark": {
            "track_count": int(benchmark.get("anchor_count", len(benchmark.get("rows", [])))),
            "average_score": benchmark_average,
            "weakest_tracks": [
                {
                    "track_id": str(item.get("source_track_id", "")).strip(),
                    "score": float(item.get("selected_score", 0.0)),
                    "notes": [str(note) for note in item.get("critic_notes", [])],
                }
                for item in weakest[:3]
            ],
        },
        "audio": {
            "covered_track_count": len(audio_coverage),
            "active_track_count": len(tracked_ids),
            "missing_track_ids": [track_id for track_id in tracked_ids if track_id and track_id not in audio_tracks],
        },
        "demo_smoke": demo_smoke,
        "generation_safety": generation_safety,
        "generation_safety_alerts": generation_safety_alerts,
        "top_blockers": list(dict.fromkeys(blockers))[:5],
    }


def mode_support_payload(project_root_path: Path | None = None) -> dict[str, Any] | None:
    root = project_root_path or project_root()
    report_path = root / "reports" / "planning" / "mode_support_status.json"
    if not report_path.exists():
        return None
    return load_json(report_path)


def mode_support_audit_payload(mode_id: str, project_root_path: Path | None = None) -> dict[str, Any] | None:
    root = project_root_path or project_root()
    report_path = root / "reports" / "quality" / "mode_support_audit" / f"{mode_id}_mode_support_audit.json"
    if not report_path.exists():
        return None
    return load_json(report_path)


def mode_support_benchmark_payload(mode_id: str, project_root_path: Path | None = None) -> dict[str, Any] | None:
    root = project_root_path or project_root()
    report_path = (
        root
        / "outputs"
        / "mode_support_benchmark"
        / mode_id
        / "mode_support_benchmark_manifest.json"
    )
    if not report_path.exists():
        return None
    return load_json(report_path)


def round2_expansion_payload(project_root_path: Path | None = None) -> dict[str, Any] | None:
    root = project_root_path or project_root()
    report_path = root / "reports" / "planning" / "round2_expansion_status.json"
    if not report_path.exists():
        return None
    return load_json(report_path)


def generation_safety_payload(project_root_path: Path | None = None) -> dict[str, Any] | None:
    root = project_root_path or project_root()
    report_path = root / "reports" / "planning" / "generation_safety_pilot_status.json"
    if not report_path.exists():
        return None
    return load_json(report_path)


def _demo_smoke_candidate_summary(manifest: dict[str, Any]) -> dict[str, Any]:
    selected_candidate_id = str(manifest.get("selected_candidate_id", "")).strip()
    critic_results = manifest.get("critic_results", [])
    winner = next(
        (item for item in critic_results if str(item.get("candidate_id", "")).strip() == selected_candidate_id),
        critic_results[0] if critic_results else {},
    )
    scores = winner.get("scores", {}) if isinstance(winner, dict) else {}
    notes = [str(note).strip() for note in winner.get("critic_notes", []) if str(note).strip()] if isinstance(winner, dict) else []
    if not notes:
        notes = [str(note).strip() for note in winner.get("demo_notes", []) if str(note).strip()] if isinstance(winner, dict) else []
    return {
        "mode_id": str(manifest.get("mode_id", "")).strip(),
        "generation_mode": str(manifest.get("generation_mode", "")).strip(),
        "requested_generation_mode": str(manifest.get("requested_generation_mode", "")).strip(),
        "fallback_reason": str(manifest.get("generation_fallback_reason", "")).strip(),
        "selected_demo_adjusted_score": float(
            manifest.get("selected_demo_adjusted_score", scores.get("demo_adjusted_total", scores.get("adjusted_total", 0.0)))
        ),
        "selected_score": float(manifest.get("selected_score", scores.get("total", 0.0))),
        "release_score": float(scores.get("release_score", 0.0)),
        "imagery_specificity_score": float(scores.get("imagery_specificity_score", 0.0)),
        "title_binding_score": float(scores.get("title_binding_score", 0.0)),
        "notes": notes,
        "manifest_path": str(manifest.get("manifest_path") or ""),
    }


def demo_smoke_payload(artist_id: str, project_root_path: Path | None = None) -> dict[str, Any]:
    root = project_root_path or project_root()
    outputs_root = root / "outputs"
    runs: list[dict[str, Any]] = []
    latest_by_mode: dict[str, dict[str, Any]] = {}
    if outputs_root.exists():
        for smoke_dir in sorted(outputs_root.glob("demo_smoke*")):
            for manifest_path in smoke_dir.glob(f"{artist_id}/*/run_manifest.json"):
                try:
                    manifest = load_json(manifest_path)
                except (OSError, json.JSONDecodeError, TypeError, ValueError):
                    continue
                summary = _demo_smoke_candidate_summary(manifest)
                summary["manifest_path"] = str(manifest_path)
                runs.append(summary)
                mode_id = summary["mode_id"] or manifest_path.parent.name
                previous = latest_by_mode.get(mode_id)
                if previous is None or manifest_path.stat().st_mtime > Path(previous["manifest_path"]).stat().st_mtime:
                    latest_by_mode[mode_id] = summary
    return {
        "run_count": len(runs),
        "latest_runs": sorted(latest_by_mode.values(), key=lambda item: item["mode_id"]),
    }


def build_engine_health(artist_ids: list[str], project_root_path: Path | None = None) -> dict[str, Any]:
    root = project_root_path or project_root()
    audio_tracks = audio_index(root)
    generation_safety = generation_safety_payload(root) or {}
    generation_safety_by_artist = {
        str(item.get("artist_id", "")).strip(): item
        for item in generation_safety.get("artists", [])
        if str(item.get("artist_id", "")).strip()
    }
    artists = [build_artist_health(artist_id, audio_tracks, generation_safety_by_artist, project_root_path=root) for artist_id in artist_ids]
    mode_support = mode_support_payload(root) or {}
    mode_audits = []
    for mode in mode_support.get("modes", []):
        mode_id = str(mode.get("mode_id", "")).strip()
        if not mode_id:
            continue
        audit = mode_support_audit_payload(mode_id, root)
        if not audit:
            continue
        mode_audits.append(
            {
                "mode_id": mode_id,
                "record_count": int(audit.get("record_count", 0)),
                "gold_count": int(audit.get("gold_count", 0)),
                "usable_count": int(audit.get("usable_count", 0)),
                "weak_count": int(audit.get("weak_count", 0)),
                "average_score": float(audit.get("average_score", 0.0)),
            }
        )
    mode_benchmarks = []
    for mode in mode_support.get("modes", []):
        mode_id = str(mode.get("mode_id", "")).strip()
        if not mode_id:
            continue
        benchmark = mode_support_benchmark_payload(mode_id, root)
        if not benchmark:
            continue
        runs = list(benchmark.get("runs", []))
        weakest = sorted(runs, key=lambda item: float(item.get("selected_score", 0.0)))[:2]
        mode_benchmarks.append(
            {
                "mode_id": mode_id,
                "track_count": int(benchmark.get("track_count", 0)),
                "average_score": float(benchmark.get("average_score", 0.0)),
                "weakest_tracks": [
                    {
                        "track_id": str(item.get("track_id", "")).strip(),
                        "score": float(item.get("selected_score", 0.0)),
                        "notes": [str(note) for note in item.get("critic_notes", []) if str(note).strip()],
                    }
                    for item in weakest
                ],
            }
        )
    hard_case_path = root / "data" / "_global" / "hard_case_registry.json"
    hard_case_registry = load_json(hard_case_path) if hard_case_path.exists() else {}
    hard_case_artists = hard_case_registry.get("artists", [])
    round2 = round2_expansion_payload(root) or {}
    return {
        "schema_version": "1.0",
        "artists": artists,
        "mode_support": {
            "mode_count": len(mode_support.get("modes", [])),
            "pending_artist_count": sum(int(mode.get("pending_artist_count", 0)) for mode in mode_support.get("modes", [])),
            "scaffolded_artist_count": sum(int(mode.get("scaffolded_artist_count", 0)) for mode in mode_support.get("modes", [])),
            "ready_artist_count": sum(int(mode.get("ready_artist_count", 0)) for mode in mode_support.get("modes", [])),
            "audits": mode_audits,
            "benchmarks": mode_benchmarks,
        },
        "hard_case": {
            "artist_count": len(hard_case_artists),
            "open_track_count": sum(
                sum(
                    1
                    for track in item.get("tracks", [])
                    if str(track.get("status", "")).strip() == "open"
                )
                for item in hard_case_artists
            ),
            "resolved_track_count": sum(
                sum(
                    1
                    for track in item.get("tracks", [])
                    if str(track.get("status", "")).strip() == "resolved"
                )
                for item in hard_case_artists
            ),
            "deferred_track_count": sum(
                sum(
                    1
                    for track in item.get("tracks", [])
                    if str(track.get("status", "")).strip() == "deferred"
                )
                for item in hard_case_artists
            ),
        },
        "round2_expansion": {
            "artist_count": int(round2.get("artist_count", 0)),
            "candidate_count": int(round2.get("candidate_count", 0)),
            "seed_count": int(round2.get("seed_count", 0)),
            "scaffolded_count": int(round2.get("scaffolded_count", 0)),
            "candidate_only_count": int(round2.get("candidate_only_count", 0)),
            "completed_count": int(round2.get("completed_count", 0)),
            "artists": [
                {
                    "artist_id": str(item.get("artist_id", "")).strip(),
                    "candidate_count": int(item.get("candidate_count", 0)),
                    "seeded_count": int(item.get("seeded_count", 0)),
                    "scaffolded_count": int(item.get("scaffolded_count", 0)),
                    "candidate_only_count": int(item.get("candidate_only_count", 0)),
                    "completed_count": int(item.get("completed_count", 0)),
                    "gold_count": int(item.get("gold_count", 0)),
                    "usable_count": int(item.get("usable_count", 0)),
                    "weak_count": int(item.get("weak_count", 0)),
                    "average_score": float(item.get("average_score", 0.0)),
                    "high_priority_count": int(item.get("high_priority_count", 0)),
                }
                for item in round2.get("artists", [])
            ],
        },
        "generation_safety": {
            "target_record_count": int(generation_safety.get("target_record_count", 0)),
            "modified_count": int(generation_safety.get("modified_count", 0)),
            "invalid_count": int(generation_safety.get("verdict_counts", {}).get("invalid", 0)),
            "audit_only_count": int(generation_safety.get("verdict_counts", {}).get("audit_only", 0)),
            "planner_safe_count": int(generation_safety.get("verdict_counts", {}).get("planner_safe", 0)),
            "generation_safe_count": int(generation_safety.get("verdict_counts", {}).get("generation_safe", 0)),
            "benchmark_safe_count": int(generation_safety.get("verdict_counts", {}).get("benchmark_safe", 0)),
            "top_blockers": list(generation_safety.get("top_blockers", [])),
        },
    }


def render_engine_health_markdown(payload: dict[str, Any]) -> str:
    lines = ["# Engine Health", ""]
    for artist in payload.get("artists", []):
        lines.extend(
            [
                f"## {artist['artist_id']}",
                "",
                f"- Conditioning: `{artist['conditioning']['average_score']}` avg / gold `{artist['conditioning']['gold_count']}` / usable `{artist['conditioning']['usable_count']}` / weak `{artist['conditioning']['weak_count']}`",
                f"- Producer expansion: `{artist['producer_expansion']['average_score']}` avg / gold `{artist['producer_expansion']['gold_count']}` / usable `{artist['producer_expansion']['usable_count']}` / weak `{artist['producer_expansion']['weak_count']}`",
                f"- Benchmark: `{artist['benchmark']['average_score']}` avg across `{artist['benchmark']['track_count']}` tracks",
                f"- Audio coverage: `{artist['audio']['covered_track_count']}/{artist['audio']['active_track_count']}`",
                f"- Conditioning audit: `{artist['conditioning_audit_path']}`",
                f"- Benchmark manifest: `{artist['benchmark_manifest_path']}`",
                f"- Generation safety: planner_safe `{artist['generation_safety']['planner_safe_count']}` / generation_safe `{artist['generation_safety']['generation_safe_count']}` / benchmark_safe `{artist['generation_safety']['benchmark_safe_count']}` / audit_only `{artist['generation_safety']['audit_only_count']}` / invalid `{artist['generation_safety']['invalid_count']}`",
                "",
                "### Demo Smoke",
                "",
            ]
        )
        demo_runs = artist.get("demo_smoke", {}).get("latest_runs", [])
        if demo_runs:
            for run in demo_runs:
                note_text = "; ".join(run.get("notes", [])) if run.get("notes") else "none"
                lines.append(
                    f"- `{run['mode_id']}` / mode `{run['generation_mode']}` / adjusted `{run['selected_demo_adjusted_score']}` / release `{run['release_score']}` / imagery `{run['imagery_specificity_score']}` / {note_text}"
                )
        else:
            lines.append("- none")
        lines.extend(
            [
                "",
                "### Generation Safety Alerts",
                "",
            ]
        )
        generation_safety_alerts = artist.get("generation_safety_alerts", [])
        if generation_safety_alerts:
            for alert in generation_safety_alerts:
                lines.append(f"- {alert}")
        else:
            lines.append("- none")
        lines.extend(
            [
                "",
                "### Top Blockers",
                "",
            ]
        )
        blockers = artist.get("top_blockers", [])
        if blockers:
            for blocker in blockers:
                lines.append(f"- {blocker}")
        else:
            lines.append("- none")
        lines.extend(["", "### Weakest Tracks", ""])
        for item in artist.get("benchmark", {}).get("weakest_tracks", []):
            note_text = "; ".join(item.get("notes", [])) if item.get("notes") else "none"
            lines.append(f"- `{item['track_id']}` / `{item['score']}` / {note_text}")
        lines.append("")
    mode_support = payload.get("mode_support", {})
    if mode_support:
        lines.extend(
            [
                "## mode_support",
                "",
                f"- Modes: `{mode_support.get('mode_count', 0)}`",
                f"- Pending artist curation: `{mode_support.get('pending_artist_count', 0)}`",
                f"- Scaffolded: `{mode_support.get('scaffolded_artist_count', 0)}`",
                f"- Ready for scaffold: `{mode_support.get('ready_artist_count', 0)}`",
                "",
            ]
        )
        for audit in mode_support.get("audits", []):
            lines.append(
                f"- `{audit['mode_id']}` / avg `{audit['average_score']}` / gold `{audit['gold_count']}` / usable `{audit['usable_count']}` / weak `{audit['weak_count']}`"
            )
        for benchmark in mode_support.get("benchmarks", []):
            weakest = benchmark.get("weakest_tracks", [])
            weakest_text = ", ".join(
                f"{item['track_id']}:{item['score']}" for item in weakest
            ) if weakest else "none"
            lines.append(
                f"- `{benchmark['mode_id']}` benchmark / avg `{benchmark['average_score']}` / tracks `{benchmark['track_count']}` / weakest `{weakest_text}`"
            )
        lines.append("")
    hard_case = payload.get("hard_case", {})
    if hard_case:
        lines.extend(
            [
                "## hard_case",
                "",
                f"- Artists: `{hard_case.get('artist_count', 0)}`",
                f"- Open tracks: `{hard_case.get('open_track_count', 0)}`",
                f"- Resolved tracks: `{hard_case.get('resolved_track_count', 0)}`",
                f"- Deferred tracks: `{hard_case.get('deferred_track_count', 0)}`",
                "",
            ]
        )
    round2 = payload.get("round2_expansion", {})
    if round2:
        lines.extend(
            [
                "## round2_expansion",
                "",
                f"- Artists: `{round2.get('artist_count', 0)}`",
                f"- Candidates: `{round2.get('candidate_count', 0)}`",
                f"- Seeded: `{round2.get('seed_count', 0)}`",
                f"- Scaffolded: `{round2.get('scaffolded_count', 0)}`",
                f"- Candidate only: `{round2.get('candidate_only_count', 0)}`",
                f"- Completed: `{round2.get('completed_count', 0)}`",
                "",
            ]
        )
        for item in round2.get("artists", []):
            lines.append(
                f"- `{item['artist_id']}` / completed `{item['completed_count']}` / gold `{item['gold_count']}` / usable `{item['usable_count']}` / weak `{item['weak_count']}` / scaffolded `{item['scaffolded_count']}` / candidate only `{item['candidate_only_count']}` / high priority `{item['high_priority_count']}`"
            )
        lines.append("")
    generation_safety = payload.get("generation_safety", {})
    if generation_safety:
        lines.extend(
            [
                "## generation_safety",
                "",
                f"- Target records: `{generation_safety.get('target_record_count', 0)}`",
                f"- Modified: `{generation_safety.get('modified_count', 0)}`",
                f"- invalid `{generation_safety.get('invalid_count', 0)}` / audit_only `{generation_safety.get('audit_only_count', 0)}` / planner_safe `{generation_safety.get('planner_safe_count', 0)}` / generation_safe `{generation_safety.get('generation_safe_count', 0)}` / benchmark_safe `{generation_safety.get('benchmark_safe_count', 0)}`",
                "",
            ]
        )
        blockers = generation_safety.get("top_blockers", [])
        if blockers:
            for item in blockers:
                lines.append(f"- `{item.get('blocker', '')}` / `{item.get('count', 0)}`")
            lines.append("")
    return "\n".join(lines)
