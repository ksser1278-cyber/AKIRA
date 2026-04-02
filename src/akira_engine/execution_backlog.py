from __future__ import annotations

from pathlib import Path
from typing import Any

from .manifest_tools import load_json


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def build_execution_backlog() -> dict[str, Any]:
    root = project_root()
    health = load_json(root / "reports" / "health" / "engine_health.json")
    producer_expansion = load_json(root / "data" / "anchor_sets" / "producer_expansion_set.json")
    producer_expansion_status = load_json(root / "reports" / "planning" / "producer_expansion_status.json")
    mode_support_status = load_json(root / "reports" / "planning" / "mode_support_status.json")
    hard_case_status = load_json(root / "reports" / "planning" / "hard_case_status.json")
    round2_status = load_json(root / "reports" / "planning" / "round2_expansion_status.json")
    phase1_blocked_path = root / "reports" / "planning" / "generation_safety_phase1_blocked.json"
    phase1_blocked = load_json(phase1_blocked_path) if phase1_blocked_path.exists() else {}
    phase1_reopen_path = root / "reports" / "planning" / "generation_safety_phase1_reopen_assessment.json"
    phase1_reopen = load_json(phase1_reopen_path) if phase1_reopen_path.exists() else {}
    remaining_source_path = root / "reports" / "planning" / "generation_safety_remaining_source_acquisition.json"
    remaining_source = load_json(remaining_source_path) if remaining_source_path.exists() else {}
    remaining_source_by_artist = {
        str(artist.get("artist_id", "")).strip(): artist
        for artist in remaining_source.get("artists", [])
        if str(artist.get("artist_id", "")).strip()
    }

    internal_tasks: list[dict[str, Any]] = []
    external_tasks: list[dict[str, Any]] = []
    deferred_tracks: set[tuple[str, str]] = set()
    resolved_tracks: set[tuple[str, str]] = set()
    hard_case_artists: set[str] = {
        str(artist.get("artist_id", "")).strip()
        for artist in hard_case_status.get("artists", [])
        if any(
            str(item.get("status", "")).strip() == "open"
            and str(item.get("track_id", "")).strip()
            for item in artist.get("tracks", [])
        )
    }
    for artist in hard_case_status.get("artists", []):
        artist_id = str(artist.get("artist_id", "")).strip()
        for item in artist.get("tracks", []):
            track_id = str(item.get("track_id", "")).strip()
            if str(item.get("status", "")).strip() == "deferred" and track_id:
                deferred_tracks.add((artist_id, track_id))
            if str(item.get("status", "")).strip() == "resolved" and track_id:
                resolved_tracks.add((artist_id, track_id))

    for artist in health.get("artists", []):
        artist_id = str(artist.get("artist_id", "")).strip()
        blockers = [str(item).strip() for item in artist.get("top_blockers", []) if str(item).strip()]
        weakest_tracks = artist.get("benchmark", {}).get("weakest_tracks", [])
        demo_runs = artist.get("demo_smoke", {}).get("latest_runs", [])
        generation_safety = artist.get("generation_safety", {}) if isinstance(artist.get("generation_safety", {}), dict) else {}
        has_remaining_source_recovery = artist_id in remaining_source_by_artist
        actionable_weakest_tracks = [
            item
            for item in weakest_tracks
            if (artist_id, str(item.get("track_id", "")).strip()) not in deferred_tracks
            and (artist_id, str(item.get("track_id", "")).strip()) not in resolved_tracks
        ]
        benchmark_blockers = [
            blocker for blocker in blockers
            if "phrasing" in blocker or "benchmark" in blocker
        ]

        if benchmark_blockers and actionable_weakest_tracks and artist_id not in hard_case_artists:
            internal_tasks.append(
                {
                    "artist_id": artist_id,
                    "task_type": "engine",
                    "priority": "high",
                    "summary": "; ".join(benchmark_blockers),
                    "track_ids": [
                        str(item.get("track_id", "")).strip()
                        for item in actionable_weakest_tracks
                        if str(item.get("track_id", "")).strip()
                    ],
                }
            )

        for item in actionable_weakest_tracks:
            track_id = str(item.get("track_id", "")).strip()
            notes = [str(note).strip() for note in item.get("notes", []) if str(note).strip()]
            if notes:
                external_tasks.append(
                    {
                        "artist_id": artist_id,
                        "track_id": track_id,
                        "priority": "high" if float(item.get("score", 0.0)) < 90 else "medium",
                        "summary": "; ".join(notes),
                        "delegate_to": "gemini",
                    }
                )

        if not demo_runs:
            internal_tasks.append(
                {
                    "artist_id": artist_id,
                    "task_type": "demo_smoke",
                    "priority": "medium",
                    "summary": "run artist demo smoke coverage",
                    "track_ids": ["smoke:not_run"],
                }
            )
        else:
            failing_demo_runs = [
                run
                for run in demo_runs
                if float(run.get("selected_demo_adjusted_score", 0.0)) < 85
                or float(run.get("release_score", 0.0)) < 0.8
                or float(run.get("imagery_specificity_score", 0.0)) < 0.7
            ]
            if failing_demo_runs:
                demo_notes = list(
                    dict.fromkeys(
                        note
                        for run in failing_demo_runs
                        for note in run.get("notes", [])
                        if str(note).strip()
                    )
                )
                internal_tasks.append(
                    {
                        "artist_id": artist_id,
                        "task_type": "demo_renderer",
                        "priority": "high",
                        "summary": "; ".join(demo_notes[:3]) or "demo smoke follow-up required",
                        "track_ids": [
                            f"{run.get('mode_id', 'unknown')}:{run.get('selected_demo_adjusted_score', 0.0)}"
                            for run in failing_demo_runs
                        ],
                    }
                )

        invalid_count = int(generation_safety.get("invalid_count", 0))
        audit_only_count = int(generation_safety.get("audit_only_count", 0))
        planner_safe_count = int(generation_safety.get("planner_safe_count", 0))
        generation_safe_count = int(generation_safety.get("generation_safe_count", 0))

        if invalid_count > 0 and not has_remaining_source_recovery:
            internal_tasks.append(
                {
                    "artist_id": artist_id,
                    "task_type": "generation_safety_relabel",
                    "priority": "high",
                    "summary": "resolve invalid generation_safety labels before runtime use",
                    "track_ids": [f"invalid:{invalid_count}"],
                }
            )
            external_tasks.append(
                {
                    "artist_id": artist_id,
                    "track_id": f"generation_safety_invalid:{invalid_count}",
                    "priority": "medium",
                    "summary": "review invalid generation_safety labels and missing evidence in pilot relabel",
                    "delegate_to": "gemini",
                }
            )

        if audit_only_count > 0 and not has_remaining_source_recovery:
            internal_tasks.append(
                {
                    "artist_id": artist_id,
                    "task_type": "generation_safety_promotion",
                    "priority": "medium",
                    "summary": "promote audit-only records to planner-safe or keep them out of runtime",
                    "track_ids": [f"audit_only:{audit_only_count}", f"planner_safe:{planner_safe_count}"],
                }
            )

        if planner_safe_count > 0 and generation_safe_count == 0:
            internal_tasks.append(
                {
                    "artist_id": artist_id,
                    "task_type": "generation_safety_runtime_block",
                    "priority": "medium",
                    "summary": "planner-safe records exist but runtime-safe set is still empty",
                    "track_ids": [f"planner_safe:{planner_safe_count}", f"generation_safe:{generation_safe_count}"],
                }
            )

    for artist in hard_case_status.get("artists", []):
        artist_id = str(artist.get("artist_id", "")).strip()
        open_tracks = [
            str(item.get("track_id", "")).strip()
            for item in artist.get("tracks", [])
            if str(item.get("status", "")).strip() == "open" and str(item.get("track_id", "")).strip()
        ]
        if open_tracks:
            internal_tasks.append(
                {
                    "artist_id": artist_id,
                    "task_type": "hard_case",
                    "priority": "high" if artist_id == "deco27" else "medium",
                    "summary": "resolve isolated benchmark hard cases without moving the baseline",
                    "track_ids": open_tracks,
                }
            )

    status_by_artist = {
        str(block.get("artist_id", "")).strip(): block
        for block in producer_expansion_status.get("artists", [])
        if str(block.get("artist_id", "")).strip()
    }

    for artist_block in producer_expansion.get("artists", []):
        artist_id = str(artist_block.get("artist_id", "")).strip()
        track_ids = [str(track_id).strip() for track_id in artist_block.get("track_ids", []) if str(track_id).strip()]
        status_block = status_by_artist.get(artist_id, {})
        health_artist = next(
            (item for item in health.get("artists", []) if str(item.get("artist_id", "")).strip() == artist_id),
            {},
        )
        producer_expansion_weak = int(health_artist.get("producer_expansion", {}).get("weak_count", 0))
        scaffolded_track_ids = [
            str(item.get("track_id", "")).strip()
            for item in status_block.get("tracks", [])
            if str(item.get("queue_status", "")).strip() == "scaffolded" and str(item.get("track_id", "")).strip()
        ]
        if track_ids and producer_expansion_weak > 0:
            internal_tasks.append(
                {
                    "artist_id": artist_id,
                    "task_type": "dataset_expansion",
                    "priority": "medium",
                    "summary": "promote producer expansion conditioning from scaffolded to usable",
                    "track_ids": track_ids,
                }
            )
        if scaffolded_track_ids and producer_expansion_weak > 0:
            external_tasks.append(
                {
                    "artist_id": artist_id,
                    "track_id": ",".join(scaffolded_track_ids),
                    "priority": "medium",
                    "summary": "full lyric grounding, provenance, hooks, and section analysis needed for producer expansion scaffold set",
                    "delegate_to": "gemini",
                }
            )

    for mode in mode_support_status.get("modes", []):
        mode_id = str(mode.get("mode_id", "")).strip()
        pending_artist_count = int(mode.get("pending_artist_count", 0))
        if pending_artist_count > 0:
            internal_tasks.append(
                {
                    "artist_id": "global",
                    "task_type": "mode_support",
                    "priority": "medium",
                    "summary": "curate cross-producer support queues before scaffold generation",
                    "track_ids": [mode_id],
                }
            )
            external_tasks.append(
                {
                    "artist_id": "global",
                    "track_id": mode_id,
                    "priority": "medium",
                    "summary": "curate cross-producer support candidates for this mode",
                    "delegate_to": "gemini",
                }
            )

    for artist in round2_status.get("artists", []):
        artist_id = str(artist.get("artist_id", "")).strip()
        scaffolded_count = int(artist.get("scaffolded_count", 0))
        candidate_only_count = int(artist.get("candidate_only_count", 0))
        weak_count = int(artist.get("weak_count", 0))
        if scaffolded_count > 0 and weak_count > 0:
            internal_tasks.append(
                {
                    "artist_id": artist_id,
                    "task_type": "round2_upgrade",
                    "priority": "medium",
                    "summary": "promote round2 scaffolds from weak to usable or gold",
                    "track_ids": [f"scaffolded:{scaffolded_count}", f"weak:{weak_count}"],
                }
            )
        elif candidate_only_count > 0:
            internal_tasks.append(
                {
                    "artist_id": artist_id,
                    "task_type": "round2_scaffold",
                    "priority": "medium",
                    "summary": "promote round2 candidates from queue to conditioning scaffolds",
                    "track_ids": [f"candidate_only:{candidate_only_count}"],
                }
            )
        if candidate_only_count > 0:
            external_tasks.append(
                {
                    "artist_id": artist_id,
                    "track_id": f"round2_unseeded:{candidate_only_count}",
                    "priority": "medium",
                    "summary": "add grounding and draft seeds for remaining round2 candidates",
                    "delegate_to": "gemini",
                }
            )

    phase1_reopen_by_artist = {
        str(artist.get("artist_id", "")).strip(): artist
        for artist in phase1_reopen.get("artists", [])
        if str(artist.get("artist_id", "")).strip()
    }
    for artist in phase1_blocked.get("artists", []):
        artist_id = str(artist.get("artist_id", "")).strip()
        blocked_count = int(artist.get("track_count", 0))
        if not artist_id or blocked_count <= 0:
            continue
        reopen_artist = phase1_reopen_by_artist.get(artist_id, {})
        ready_bundle_count = int(reopen_artist.get("ready_bundle_count", 0))
        normalization_pending_count = int(reopen_artist.get("normalization_pending_count", 0))
        phase1_retry_ready_count = int(reopen_artist.get("phase1_retry_ready_count", 0))
        missing_bundle_count = int(reopen_artist.get("missing_bundle_count", 0))

        if phase1_retry_ready_count >= blocked_count and blocked_count > 0:
            continue

        if ready_bundle_count > 0 and normalization_pending_count > 0:
            internal_tasks.append(
                {
                    "artist_id": artist_id,
                    "task_type": "phase1_internal_normalization",
                    "priority": "high",
                    "summary": "validated lyric source bundles are ready; normalize them into phase1 grounding patches",
                    "track_ids": [
                        f"ready_bundles:{ready_bundle_count}",
                        f"normalization_pending:{normalization_pending_count}",
                        f"phase1_retry_ready:{phase1_retry_ready_count}",
                    ],
                }
            )
            if missing_bundle_count > 0:
                external_tasks.append(
                    {
                        "artist_id": artist_id,
                        "track_id": f"lyric_grounding_source:{missing_bundle_count}",
                        "priority": "high",
                        "summary": "acquire remaining Japanese lyric grounding sources before retry",
                        "delegate_to": "gemini",
                    }
                )
            continue
        internal_tasks.append(
            {
                "artist_id": artist_id,
                "task_type": "lyric_grounding_source_block",
                "priority": "high",
                "summary": "phase1 core cleanup is blocked until Japanese lyric grounding sources are acquired",
                "track_ids": [f"blocked_phase1:{blocked_count}"],
            }
        )
        external_tasks.append(
            {
                "artist_id": artist_id,
                "track_id": f"lyric_grounding_source:{blocked_count}",
                "priority": "high",
                "summary": "acquire Japanese lyric grounding sources for blocked phase1 tracks before retry",
                "delegate_to": "gemini",
            }
        )

    for artist_id, artist in remaining_source_by_artist.items():
        track_count = int(artist.get("track_count", 0))
        if track_count <= 0:
            continue
        workflow_counts = artist.get("workflow_counts", {}) if isinstance(artist.get("workflow_counts", {}), dict) else {}
        source_only = int(workflow_counts.get("source_only", 0))
        source_plus_mode = int(workflow_counts.get("source_plus_mode", 0))
        source_plus_provenance = int(workflow_counts.get("source_plus_provenance", 0))
        internal_tasks.append(
            {
                "artist_id": artist_id,
                "task_type": "generation_safety_source_recovery",
                "priority": "high" if source_plus_provenance > 0 else "medium",
                "summary": "recover trusted lyric-source bundles for remaining non-runtime-safe conditioning records",
                "track_ids": [
                    f"tracks:{track_count}",
                    f"source_only:{source_only}",
                    f"source_plus_mode:{source_plus_mode}",
                    f"source_plus_provenance:{source_plus_provenance}",
                ],
            }
        )
        external_tasks.append(
            {
                "artist_id": artist_id,
                "track_id": f"generation_safety_source_recovery:{track_count}",
                "priority": "high" if source_plus_provenance > 0 else "medium",
                "summary": "acquire trusted lyric-source bundles for the remaining generation_safety audit-only/invalid set",
                "delegate_to": "gemini",
            }
        )

    return {
        "schema_version": "1.0",
        "record_type": "execution_backlog",
        "internal_tasks": internal_tasks,
        "external_tasks": external_tasks,
    }


def render_execution_backlog_markdown(payload: dict[str, Any]) -> str:
    lines = ["# Execution Backlog", ""]

    lines.extend(["## Internal", ""])
    for task in payload.get("internal_tasks", []):
        lines.append(
            f"- `{task['artist_id']}` / `{task['task_type']}` / `{task['priority']}` / {task['summary']} / {', '.join(task.get('track_ids', [])) or 'none'}"
        )
    if not payload.get("internal_tasks"):
        lines.append("- none")

    lines.extend(["", "## External", ""])
    for task in payload.get("external_tasks", []):
        lines.append(
            f"- `{task['artist_id']}` / `{task['track_id']}` / `{task['priority']}` / {task['summary']} / delegate `{task['delegate_to']}`"
        )
    if not payload.get("external_tasks"):
        lines.append("- none")

    lines.append("")
    return "\n".join(lines)
