from __future__ import annotations

import json
from pathlib import Path
from shutil import copy2
from typing import Any

from .generation_safety import PLACEHOLDER_PATTERNS, load_json


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _collect_placeholder_paths(value: Any, path: str = "") -> list[str]:
    hits: list[str] = []
    if isinstance(value, str):
        lowered = value.lower()
        if any(pattern in lowered for pattern in PLACEHOLDER_PATTERNS):
            hits.append(path or "<root>")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            child_path = f"{path}[{index}]" if path else f"[{index}]"
            hits.extend(_collect_placeholder_paths(item, child_path))
    elif isinstance(value, dict):
        for key, item in value.items():
            child_path = f"{path}.{key}" if path else str(key)
            hits.extend(_collect_placeholder_paths(item, child_path))
    return hits


def _target_path(root: Path, artist_id: str, track_id: str) -> Path:
    prefix = f"{artist_id}_"
    suffix = track_id[len(prefix) :] if track_id.startswith(prefix) else track_id
    return root / "data" / artist_id / "reference_tracks" / f"{suffix}.conditioning.json"


def _workflow_type(item: dict[str, Any]) -> str:
    blockers = {str(blocker).strip() for blocker in item.get("blockers", [])}
    if "missing_provenance" in blockers:
        return "provenance_plus_cleanup"
    if "mode_fit_unverified" in blockers:
        return "extended_cleanup"
    return "core_cleanup"


def build_grounding_handoff(root: Path | None = None) -> dict[str, Any]:
    root = root or project_root()
    queue_path = root / "reports" / "planning" / "generation_safety_promotion_queue.json"
    queue = load_json(queue_path)
    items = [
        item
        for item in queue.get("items", [])
        if str(item.get("promotion_class", "")).strip() == "grounding_and_surface_upgrade"
        and str(item.get("promotion_status", "")).strip() == "open"
    ]

    by_artist: dict[str, list[dict[str, Any]]] = {}
    workflow_counts = {
        "core_cleanup": 0,
        "extended_cleanup": 0,
        "provenance_plus_cleanup": 0,
    }

    for item in items:
        artist_id = str(item.get("artist_id", "")).strip()
        track_id = str(item.get("track_id", "")).strip()
        if not artist_id or not track_id:
            continue
        record_path = _target_path(root, artist_id, track_id)
        record = load_json(record_path) if record_path.exists() else {}
        workflow_type = _workflow_type(item)
        workflow_counts[workflow_type] += 1
        by_artist.setdefault(artist_id, []).append(
            {
                **item,
                "path": str(record_path),
                "workflow_type": workflow_type,
                "placeholder_field_paths": _collect_placeholder_paths(record),
            }
        )

    artists = []
    for artist_id, artist_items in sorted(by_artist.items()):
        tracks = sorted(
            artist_items,
            key=lambda item: (
                {"provenance_plus_cleanup": 0, "extended_cleanup": 1, "core_cleanup": 2}.get(
                    str(item.get("workflow_type", "")),
                    99,
                ),
                -float(item.get("score", 0.0)),
                str(item.get("track_id", "")),
            ),
        )
        artists.append(
            {
                "artist_id": artist_id,
                "track_count": len(tracks),
                "workflow_counts": {
                    "core_cleanup": sum(1 for track in tracks if track.get("workflow_type") == "core_cleanup"),
                    "extended_cleanup": sum(1 for track in tracks if track.get("workflow_type") == "extended_cleanup"),
                    "provenance_plus_cleanup": sum(
                        1 for track in tracks if track.get("workflow_type") == "provenance_plus_cleanup"
                    ),
                },
                "tracks": tracks,
            }
        )

    return {
        "schema_version": "1.0",
        "record_type": "generation_safety_grounding_handoff",
        "selected_count": len(items),
        "artist_count": len(artists),
        "workflow_counts": workflow_counts,
        "artists": artists,
    }


def render_grounding_handoff_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Generation Safety Grounding Upgrade Handoff",
        "",
        f"- selected records `{payload.get('selected_count', 0)}`",
        f"- artists `{payload.get('artist_count', 0)}`",
        f"- core_cleanup `{payload.get('workflow_counts', {}).get('core_cleanup', 0)}`",
        f"- extended_cleanup `{payload.get('workflow_counts', {}).get('extended_cleanup', 0)}`",
        f"- provenance_plus_cleanup `{payload.get('workflow_counts', {}).get('provenance_plus_cleanup', 0)}`",
        "",
        "## Scope",
        "",
        "- objective: move open `grounding_and_surface_upgrade` records from `audit_only` to `planner_safe`",
        "- submit merge-friendly JSON patches or full corrected records",
        "- validator checks the merged record, not only the patch surface",
        "- `deco27_hibana` remains the only provenance-plus-cleanup outlier",
        "",
        "## Required Result",
        "",
        "- no placeholder/scaffold language in merged record",
        "- `lyric_ground_truth.full_text_status = full`",
        "- section grounding is complete enough for `planner_safe` verdict",
        "- surface noise is removed from sections/hook lines",
        "- when `mode_fit_unverified` is present, `song_intent.narrative_role` must resolve to exactly one supported mode",
        "",
    ]
    for artist in payload.get("artists", []):
        lines.append(f"## {artist['artist_id']}")
        lines.append("")
        counts = artist.get("workflow_counts", {})
        lines.append(
            f"- core `{counts.get('core_cleanup', 0)}` / extended `{counts.get('extended_cleanup', 0)}` / provenance+ `{counts.get('provenance_plus_cleanup', 0)}`"
        )
        for track in artist.get("tracks", []):
            blockers = ", ".join(track.get("blockers", [])) or "none"
            placeholder_fields = ", ".join(track.get("placeholder_field_paths", [])[:8]) or "none"
            lines.append(
                f"- `{track['track_id']}` / workflow `{track['workflow_type']}` / blockers `{blockers}` / placeholder paths `{placeholder_fields}` / path `{track['path']}`"
            )
        lines.append("")
    return "\n".join(lines)


def render_grounding_batch_prompt(payload: dict[str, Any]) -> str:
    lines = [
        "This task is generation_safety grounding and surface upgrade batch 1.",
        "",
        "Goal:",
        "- Upgrade the remaining grounding_and_surface_upgrade records from `audit_only` toward `planner_safe` by replacing scaffold grounding, removing surface noise, and verifying mode only when required.",
        "",
        "Important:",
        "- Do not modify engine code.",
        "- Keep existing track_id values.",
        "- Submit merge-friendly JSON only.",
        "- Patch JSON is allowed if the merged record becomes planner_safe.",
        "- Validator evaluates the merged record after patch application.",
        "",
        "Required result per record:",
        "- full grounding replaces placeholder sections and hook lines",
        "- scaffold or placeholder notes are removed or overwritten",
        "- merged record must no longer trigger `partial_grounding` or `surface_noise_risk`",
        "- if the current blocker list includes `mode_fit_unverified`, set `song_intent.narrative_role` to exactly one supported mode",
        "- if the current blocker list includes `missing_provenance`, add trusted lyric_sources and metadata_sources",
        "",
        "Workflow types:",
        f"- core_cleanup: `{payload.get('workflow_counts', {}).get('core_cleanup', 0)}`",
        f"- extended_cleanup: `{payload.get('workflow_counts', {}).get('extended_cleanup', 0)}`",
        f"- provenance_plus_cleanup: `{payload.get('workflow_counts', {}).get('provenance_plus_cleanup', 0)}`",
        "",
        "Outlier:",
        "- `deco27_hibana` still needs provenance along with grounding cleanup.",
        "",
        "Done when:",
        "- generation_safety verdict becomes at least `planner_safe` after merge and pilot recomputation.",
        "",
    ]
    for artist in payload.get("artists", []):
        lines.append(f"{artist['artist_id']}:")
        for track in artist.get("tracks", []):
            lines.append(f"- {track['track_id']} ({track['workflow_type']})")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _phase_batches(payload: dict[str, Any]) -> list[dict[str, Any]]:
    phases = [
        {
            "phase_id": "phase1_core_cleanup",
            "workflow_type": "core_cleanup",
            "description": "Records that only need scaffold grounding replacement and surface cleanup.",
        },
        {
            "phase_id": "phase2_extended_cleanup",
            "workflow_type": "extended_cleanup",
            "description": "Records that need grounding cleanup plus explicit mode verification.",
        },
        {
            "phase_id": "phase3_provenance_plus_cleanup",
            "workflow_type": "provenance_plus_cleanup",
            "description": "Outlier records that still need provenance along with grounding cleanup.",
        },
    ]
    phase_payloads: list[dict[str, Any]] = []
    for phase in phases:
        artists: list[dict[str, Any]] = []
        track_count = 0
        for artist in payload.get("artists", []):
            tracks = [track for track in artist.get("tracks", []) if track.get("workflow_type") == phase["workflow_type"]]
            if not tracks:
                continue
            track_count += len(tracks)
            artists.append(
                {
                    "artist_id": artist["artist_id"],
                    "track_count": len(tracks),
                    "tracks": tracks,
                }
            )
        phase_payloads.append(
            {
                "phase_id": phase["phase_id"],
                "workflow_type": phase["workflow_type"],
                "description": phase["description"],
                "track_count": track_count,
                "artist_count": len(artists),
                "artists": artists,
            }
        )
    return phase_payloads


def render_phase_overview_markdown(phase_payloads: list[dict[str, Any]]) -> str:
    lines = [
        "# Generation Safety Grounding Phase Overview",
        "",
    ]
    for phase in phase_payloads:
        lines.extend(
            [
                f"## {phase['phase_id']}",
                "",
                f"- workflow `{phase['workflow_type']}`",
                f"- tracks `{phase['track_count']}`",
                f"- artists `{phase['artist_count']}`",
                f"- description: {phase['description']}",
                "",
            ]
        )
        for artist in phase.get("artists", []):
            track_ids = ", ".join(str(track["track_id"]) for track in artist.get("tracks", []))
            lines.append(f"- `{artist['artist_id']}`: {track_ids}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_phase_prompt(phase_payload: dict[str, Any]) -> str:
    lines = [
        f"This task is {phase_payload['phase_id']}.",
        "",
        "Goal:",
        f"- Process only `{phase_payload['workflow_type']}` records in the generation_safety grounding queue.",
        f"- {phase_payload['description']}",
        "",
        "Important:",
        "- Do not modify engine code.",
        "- Keep existing track_id values.",
        "- Submit merge-friendly JSON only.",
        "- Patch JSON is allowed if the merged record becomes planner_safe.",
        "- Use the bundled `source_records/` copies inside each artist package as the editing reference.",
        "- Return one JSON file per track into the matching artist `incoming/` directory under this phase package.",
        "- Do not submit mojibake, replacement characters, broken byte sequences, or unreadable text.",
        "- Do not replace placeholders with generic English summaries or meta commentary.",
        "- Do not replace placeholders with inferred paraphrases; edited `sections` and `hook_lines` must use clean grounded Japanese text copied or tightly aligned from bundled `source_records/`.",
        "- Do not add English cleanup commentary to `source_provenance.notes`, `song_intent.emotional_thesis`, or `lyric_ground_truth.copyright_handling_note`.",
        "- Before submission, verify zero replacement characters, zero mojibake, zero scaffold phrases, and zero English/meta commentary anywhere in edited fields.",
        "- If a track cannot be grounded into clean UTF-8 text aligned to the bundled source record, leave it unsubmitted.",
        "",
    ]
    workflow_type = str(phase_payload.get("workflow_type", ""))
    if workflow_type == "core_cleanup":
        lines.extend(
            [
                "Required result per record:",
                "- replace placeholder section lines and hook lines with section-complete grounding",
                "- remove scaffold and placeholder language from notes and lyric fields",
                "- keep narrative_role and provenance unchanged unless the bundled record itself proves they are wrong",
                "- keep sections and hook lines free of mojibake and generic English rewrite lines",
                "- keep notes, thesis, and copyright fields free of English cleanup commentary",
                "- merged record must no longer trigger `partial_grounding` or `surface_noise_risk`",
                "",
            ]
        )
    elif workflow_type == "extended_cleanup":
        lines.extend(
            [
                "Required result per record:",
                "- replace placeholder section lines and hook lines with section-complete grounding",
                "- remove scaffold and placeholder language from notes and lyric fields",
                "- set `song_intent.narrative_role` to exactly one supported mode",
                "- merged record must no longer trigger `partial_grounding`, `surface_noise_risk`, or `mode_fit_unverified`",
                "",
            ]
        )
    else:
        lines.extend(
            [
                "Required result per record:",
                "- replace placeholder section lines and hook lines with section-complete grounding",
                "- remove scaffold and placeholder language from notes and lyric fields",
                "- add trusted lyric_sources and metadata_sources",
                "- set `song_intent.narrative_role` to exactly one supported mode",
                "- merged record must no longer trigger `missing_provenance`, `partial_grounding`, `surface_noise_risk`, or `mode_fit_unverified`",
                "",
            ]
        )
    lines.extend(
        [
            "Submission format:",
            "- one merge-friendly JSON patch per track",
            "- filename pattern: `<track_id>.json`",
            "- update only the fields needed to clear the listed blockers",
            "",
        ]
    )
    lines.append("Tracks:")
    for artist in phase_payload.get("artists", []):
        lines.append(f"{artist['artist_id']}:")
        for track in artist.get("tracks", []):
            lines.append(f"- {track['track_id']}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _render_phase_artist_packet_md(artist_id: str, phase_id: str, tracks: list[dict[str, Any]]) -> str:
    lines = [
        f"# {phase_id} Packet: {artist_id}",
        "",
        f"- track count `{len(tracks)}`",
        "",
    ]
    for track in tracks:
        lines.extend(
            [
                f"## {track['track_id']}",
                "",
                f"- workflow `{track['workflow_type']}`",
                f"- score `{track['score']}`",
                f"- blockers `{', '.join(track.get('blockers', [])) or 'none'}`",
                f"- recommended action `{track.get('recommended_next_action', '')}`",
                f"- placeholder paths `{', '.join(track.get('placeholder_field_paths', [])) or 'none'}`",
                f"- source record `{track.get('source_record_path', '')}`",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def _render_phase_artist_brief_md(phase_payload: dict[str, Any], artist_id: str) -> str:
    workflow_type = str(phase_payload.get("workflow_type", ""))
    lines = [
        f"# {phase_payload['phase_id']} Brief: {artist_id}",
        "",
        f"- workflow `{workflow_type}`",
        "- keep track_id stable",
        "- submit merge-friendly JSON only",
        "- use bundled `source_records/` copies in this package as the reference input",
        "- write output patches to this package's `incoming/` directory",
        "- do not submit mojibake, unreadable text, or generic English summary lines",
        "- do not replace placeholders with inferred paraphrases; use grounded Japanese text copied or tightly aligned from bundled `source_records/`",
        "- do not add English cleanup commentary to notes, thesis, or copyright fields",
    ]
    if workflow_type == "core_cleanup":
        lines.extend(
            [
                "- replace placeholder/scaffold text with section-complete grounding",
                "- remove surface-noise lines from sections and hook_lines",
                "- do not change narrative_role unless local evidence forces correction",
            ]
        )
    elif workflow_type == "extended_cleanup":
        lines.extend(
            [
                "- replace placeholder/scaffold text with section-complete grounding",
                "- remove surface-noise lines from sections and hook_lines",
                "- set song_intent.narrative_role to exactly one supported mode",
            ]
        )
    else:
        lines.extend(
            [
                "- replace placeholder/scaffold text with section-complete grounding",
                "- remove surface-noise lines from sections and hook_lines",
                "- add trusted lyric_sources and metadata_sources",
                "- set song_intent.narrative_role to exactly one supported mode",
            ]
        )
    lines.append("")
    return "\n".join(lines)


def _prepare_phase_artist_tracks(artist_dir: Path, tracks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    source_records_dir = artist_dir / "source_records"
    source_records_dir.mkdir(parents=True, exist_ok=True)
    prepared_tracks: list[dict[str, Any]] = []
    for track in tracks:
        source_path = Path(str(track.get("path", "")))
        bundled_name = f"{track['track_id']}.conditioning.json"
        bundled_path = source_records_dir / bundled_name
        if source_path.exists():
            copy2(source_path, bundled_path)
        prepared_track = {key: value for key, value in track.items() if key != "path"}
        prepared_track["source_record_path"] = str(Path("source_records") / bundled_name)
        prepared_tracks.append(prepared_track)
    return prepared_tracks


def _write_phase_assets(data_root: Path, phase_payloads: list[dict[str, Any]]) -> None:
    for phase in phase_payloads:
        phase_dir = data_root / str(phase["phase_id"])
        phase_dir.mkdir(parents=True, exist_ok=True)
        (phase_dir / "prompt.txt").write_text(render_phase_prompt(phase), encoding="utf-8")
        overview = {
            "phase_id": phase["phase_id"],
            "workflow_type": phase["workflow_type"],
            "description": phase["description"],
            "track_count": phase["track_count"],
            "artist_count": phase["artist_count"],
            "artists": phase["artists"],
        }
        (phase_dir / "overview.json").write_text(json.dumps(overview, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        overview_md_lines = [
            f"# {phase['phase_id']}",
            "",
            f"- workflow `{phase['workflow_type']}`",
            f"- tracks `{phase['track_count']}`",
            f"- artists `{phase['artist_count']}`",
            f"- description: {phase['description']}",
            "",
        ]
        for artist in phase.get("artists", []):
            track_ids = ", ".join(str(track["track_id"]) for track in artist.get("tracks", []))
            overview_md_lines.append(f"- `{artist['artist_id']}`: {track_ids}")
        overview_md_lines.append("")
        (phase_dir / "overview.md").write_text("\n".join(overview_md_lines), encoding="utf-8")

        for artist in phase.get("artists", []):
            artist_dir = phase_dir / str(artist["artist_id"])
            artist_dir.mkdir(parents=True, exist_ok=True)
            (artist_dir / "incoming").mkdir(parents=True, exist_ok=True)
            prepared_tracks = _prepare_phase_artist_tracks(artist_dir, artist["tracks"])
            packet_json = {
                "schema_version": "1.0",
                "phase_id": phase["phase_id"],
                "artist_id": artist["artist_id"],
                "track_count": artist["track_count"],
                "source_records_dir": str(Path("source_records")),
                "tracks": prepared_tracks,
            }
            (artist_dir / "packet.json").write_text(json.dumps(packet_json, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            (artist_dir / "packet.md").write_text(
                _render_phase_artist_packet_md(str(artist["artist_id"]), str(phase["phase_id"]), prepared_tracks),
                encoding="utf-8",
            )
            (artist_dir / "brief.md").write_text(
                _render_phase_artist_brief_md(phase, str(artist["artist_id"])),
                encoding="utf-8",
            )


def write_grounding_handoff(root: Path | None = None) -> dict[str, Any]:
    root = root or project_root()
    payload = build_grounding_handoff(root)
    report_dir = root / "reports" / "planning"
    data_root = root / "data" / "_global" / "generation_safety_grounding_upgrade"
    report_dir.mkdir(parents=True, exist_ok=True)
    data_root.mkdir(parents=True, exist_ok=True)

    handoff_json = report_dir / "generation_safety_grounding_handoff.json"
    handoff_md = report_dir / "generation_safety_grounding_handoff.md"
    handoff_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    handoff_md.write_text(render_grounding_handoff_markdown(payload), encoding="utf-8")
    (data_root / "batch_delegation_prompt.txt").write_text(render_grounding_batch_prompt(payload), encoding="utf-8")
    phase_payloads = _phase_batches(payload)
    (data_root / "phase_batches.json").write_text(json.dumps(phase_payloads, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (data_root / "phase_batches.md").write_text(render_phase_overview_markdown(phase_payloads), encoding="utf-8")
    for phase in phase_payloads:
        prompt_name = f"{phase['phase_id']}.prompt.txt"
        (data_root / prompt_name).write_text(render_phase_prompt(phase), encoding="utf-8")
    _write_phase_assets(data_root, phase_payloads)

    for artist in payload.get("artists", []):
        artist_dir = data_root / str(artist["artist_id"])
        artist_dir.mkdir(parents=True, exist_ok=True)
        (artist_dir / "incoming").mkdir(parents=True, exist_ok=True)
        packet_json = {
            "schema_version": "1.0",
            "artist_id": artist["artist_id"],
            "track_count": artist["track_count"],
            "workflow_counts": artist["workflow_counts"],
            "tracks": artist["tracks"],
        }
        (artist_dir / "packet.json").write_text(json.dumps(packet_json, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        packet_lines = [
            f"# Generation Safety Grounding Packet: {artist['artist_id']}",
            "",
            f"- track count `{artist['track_count']}`",
            f"- core `{artist['workflow_counts'].get('core_cleanup', 0)}`",
            f"- extended `{artist['workflow_counts'].get('extended_cleanup', 0)}`",
            f"- provenance+ `{artist['workflow_counts'].get('provenance_plus_cleanup', 0)}`",
            "",
        ]
        for track in artist.get("tracks", []):
            packet_lines.extend(
                [
                    f"## {track['track_id']}",
                    "",
                    f"- workflow `{track['workflow_type']}`",
                    f"- score `{track['score']}`",
                    f"- blockers `{', '.join(track.get('blockers', [])) or 'none'}`",
                    f"- recommended action `{track.get('recommended_next_action', '')}`",
                    f"- placeholder paths `{', '.join(track.get('placeholder_field_paths', [])) or 'none'}`",
                    f"- target path `{track['path']}`",
                    "",
                ]
            )
        (artist_dir / "packet.md").write_text("\n".join(packet_lines).rstrip() + "\n", encoding="utf-8")
        brief_lines = [
            f"# Grounding Upgrade Brief: {artist['artist_id']}",
            "",
            "- replace placeholder/scaffold text with section-complete grounding",
            "- remove surface-noise lines from sections and hook_lines",
            "- keep track_id stable and submit merge-friendly JSON",
            "- only touch narrative_role when `mode_fit_unverified` is present",
            "- add provenance only for records that still carry `missing_provenance`",
            "",
        ]
        (artist_dir / "brief.md").write_text("\n".join(brief_lines).rstrip() + "\n", encoding="utf-8")

    return payload
