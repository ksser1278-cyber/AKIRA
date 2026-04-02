from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from .reporting import load_json, write_utf8_json, write_utf8_text


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _track_suffix(artist_id: str, track_id: str) -> str:
    prefix = f"{artist_id}_"
    if track_id.startswith(prefix):
        return track_id[len(prefix) :]
    return track_id


def _current_record_path(root: Path, artist_id: str, track_id: str) -> Path:
    return root / "data" / artist_id / "reference_tracks" / f"{_track_suffix(artist_id, track_id)}.conditioning.json"


def _bundle_path(root: Path, artist_id: str, track_id: str) -> Path:
    return (
        root
        / "data"
        / "_global"
        / "generation_safety_lyric_grounding_source_acquisition"
        / artist_id
        / "incoming"
        / f"{track_id}.json"
    )


def _consume_bundle_sections(current_sections: list[dict[str, Any]], bundle_sections: list[dict[str, Any]]) -> list[str]:
    remaining = Counter(str(section.get("section_type", "")).strip() for section in bundle_sections if str(section.get("section_type", "")).strip())
    unresolved: list[str] = []
    for section in current_sections:
        section_type = str(section.get("section_type", "")).strip()
        section_name = str(section.get("section_name", "")).strip() or section_type or "unknown"
        if remaining.get(section_type, 0) > 0:
            remaining[section_type] -= 1
        else:
            unresolved.append(section_name)
    return unresolved


def _track_entry(root: Path, artist_id: str, track_id: str, ready_tracks: set[str]) -> dict[str, Any]:
    current_path = _current_record_path(root, artist_id, track_id)
    bundle_path = _bundle_path(root, artist_id, track_id)
    current_record = load_json(current_path) if current_path.exists() else {}
    bundle_record = load_json(bundle_path) if bundle_path.exists() else {}

    current_sections = current_record.get("lyric_ground_truth", {}).get("sections", []) if isinstance(current_record.get("lyric_ground_truth", {}), dict) else []
    bundle_sections = bundle_record.get("lyric_ground_truth", {}).get("sections", []) if isinstance(bundle_record.get("lyric_ground_truth", {}), dict) else []
    current_generation_safety = current_record.get("generation_safety", {}) if isinstance(current_record.get("generation_safety", {}), dict) else {}
    current_verdict = str(current_generation_safety.get("verdict", "")).strip()
    current_section_names = [str(section.get("section_name", "")).strip() for section in current_sections if isinstance(section, dict)]
    current_section_types = [str(section.get("section_type", "")).strip() for section in current_sections if isinstance(section, dict)]
    bundle_section_names = [str(section.get("section_name", "")).strip() for section in bundle_sections if isinstance(section, dict)]
    bundle_section_types = [str(section.get("section_type", "")).strip() for section in bundle_sections if isinstance(section, dict)]
    unresolved_slots = _consume_bundle_sections(current_sections, bundle_sections)
    ready_bundle = track_id in ready_tracks and bundle_path.exists()
    current_runtime_ready = current_verdict in {"planner_safe", "generation_safe", "benchmark_safe"}
    can_reopen_phase1 = current_runtime_ready or (ready_bundle and not unresolved_slots)

    blockers: list[str] = []
    if not ready_bundle:
        blockers.append("lyric_grounding_bundle_missing")
    if unresolved_slots and not current_runtime_ready:
        blockers.append("section_schema_compression")

    return {
        "track_id": track_id,
        "artist_id": artist_id,
        "current_record_path": str(current_path),
        "source_bundle_path": str(bundle_path),
        "ready_bundle": ready_bundle,
        "current_generation_safety_verdict": current_verdict,
        "can_reopen_phase1": can_reopen_phase1,
        "current_section_names": current_section_names,
        "current_section_types": current_section_types,
        "bundle_section_names": bundle_section_names,
        "bundle_section_types": bundle_section_types,
        "bundle_hook_line_count": len(bundle_record.get("lyric_ground_truth", {}).get("hook_lines", []) or [])
        if isinstance(bundle_record.get("lyric_ground_truth", {}), dict)
        else 0,
        "unresolved_section_slots": unresolved_slots,
        "blockers": blockers,
        "recommended_next_action": (
            "complete"
            if current_runtime_ready
            else "internal_normalization"
            if ready_bundle and unresolved_slots
            else "phase1_retry_ready"
            if can_reopen_phase1
            else "bundle_reacquisition"
        ),
    }


def build_phase1_reopen_assessment(root: Path | None = None) -> dict[str, Any]:
    root = root or project_root()
    blocked = load_json(root / "reports" / "planning" / "generation_safety_phase1_blocked.json")
    source_status = load_json(root / "reports" / "planning" / "generation_safety_lyric_grounding_source_status.json")
    ready_tracks = {str(item).strip() for item in source_status.get("ready_tracks", []) if str(item).strip()}

    artists: list[dict[str, Any]] = []
    total_tracks = 0
    ready_bundle_count = 0
    normalization_pending_count = 0
    phase1_retry_ready_count = 0
    missing_bundle_count = 0

    for artist in blocked.get("artists", []):
        artist_id = str(artist.get("artist_id", "")).strip()
        track_ids = [str(track_id).strip() for track_id in artist.get("tracks", []) if str(track_id).strip()]
        if not artist_id or not track_ids:
            continue
        entries = [_track_entry(root, artist_id, track_id, ready_tracks) for track_id in track_ids]
        artist_ready = sum(1 for entry in entries if entry["ready_bundle"])
        artist_retry_ready = sum(1 for entry in entries if entry["can_reopen_phase1"])
        artist_missing = sum(1 for entry in entries if "lyric_grounding_bundle_missing" in entry["blockers"])
        artist_norm_pending = sum(1 for entry in entries if entry["recommended_next_action"] == "internal_normalization")

        total_tracks += len(entries)
        ready_bundle_count += artist_ready
        phase1_retry_ready_count += artist_retry_ready
        missing_bundle_count += artist_missing
        normalization_pending_count += artist_norm_pending

        artists.append(
            {
                "artist_id": artist_id,
                "track_count": len(entries),
                "ready_bundle_count": artist_ready,
                "normalization_pending_count": artist_norm_pending,
                "phase1_retry_ready_count": artist_retry_ready,
                "missing_bundle_count": artist_missing,
                "tracks": entries,
            }
        )

    status = "phase1_retry_ready" if phase1_retry_ready_count == total_tracks else "internal_normalization_required"
    return {
        "schema_version": "1.0",
        "record_type": "generation_safety_phase1_reopen_assessment",
        "phase_id": "phase1_core_cleanup",
        "status": status,
        "track_count": total_tracks,
        "artist_count": len(artists),
        "ready_bundle_count": ready_bundle_count,
        "normalization_pending_count": normalization_pending_count,
        "phase1_retry_ready_count": phase1_retry_ready_count,
        "missing_bundle_count": missing_bundle_count,
        "artists": artists,
    }


def render_phase1_reopen_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Generation Safety Phase1 Reopen Assessment",
        "",
        f"- phase: `{payload.get('phase_id', 'phase1_core_cleanup')}`",
        f"- status: `{payload.get('status', 'unknown')}`",
        f"- tracks: `{payload.get('track_count', 0)}`",
        f"- ready bundles: `{payload.get('ready_bundle_count', 0)}`",
        f"- normalization pending: `{payload.get('normalization_pending_count', 0)}`",
        f"- phase1 retry ready: `{payload.get('phase1_retry_ready_count', 0)}`",
        "",
        "## Read",
        "",
        "- lyric grounding source acquisition is complete for the blocked phase1 set",
        "- current source bundles are valid for source policy and citation review",
        "- source bundle compression still exists at the bundle layer, but normalized current records can override that when phase1 grounding has already been merged",
        "",
    ]
    for artist in payload.get("artists", []):
        lines.extend(
            [
                f"## {artist['artist_id']}",
                "",
                f"- ready bundles `{artist.get('ready_bundle_count', 0)}`",
                f"- normalization pending `{artist.get('normalization_pending_count', 0)}`",
                f"- phase1 retry ready `{artist.get('phase1_retry_ready_count', 0)}`",
            ]
        )
        for track in artist.get("tracks", []):
            unresolved = ", ".join(track.get("unresolved_section_slots", [])) or "none"
            lines.append(
                f"- `{track['track_id']}` / current verdict `{track.get('current_generation_safety_verdict', '')}` / bundle `{', '.join(track.get('bundle_section_types', [])) or 'none'}` / current `{', '.join(track.get('current_section_types', [])) or 'none'}` / unresolved `{unresolved}` / next `{track['recommended_next_action']}`"
            )
        lines.append("")
    return "\n".join(lines)


def build_internal_normalization_overview(payload: dict[str, Any]) -> dict[str, Any]:
    artists: list[dict[str, Any]] = []
    total_pending = 0
    for artist in payload.get("artists", []):
        tracks = [track for track in artist.get("tracks", []) if track.get("recommended_next_action") == "internal_normalization"]
        if not tracks:
            continue
        total_pending += len(tracks)
        artists.append(
            {
                "artist_id": artist["artist_id"],
                "track_count": len(tracks),
                "tracks": tracks,
            }
        )
    return {
        "schema_version": "1.0",
        "record_type": "generation_safety_phase1_internal_normalization",
        "status": "open" if total_pending else "complete",
        "track_count": total_pending,
        "artist_count": len(artists),
        "artists": artists,
    }


def render_internal_normalization_overview_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Generation Safety Phase1 Internal Normalization",
        "",
        f"- status: `{payload.get('status', 'unknown')}`",
        f"- tracks: `{payload.get('track_count', 0)}`",
        f"- artists: `{payload.get('artist_count', 0)}`",
        "",
        "## Goal",
        "",
        "- take validated lyric-grounding source bundles and normalize them into phase1 grounding patches",
        "- preserve trusted lyric text while expanding from compressed `verse` / `chorus` bundle sections into the current 5-section conditioning schema",
        "",
        "## Required Internal Work",
        "",
        "- map exact lyric text from source bundles into current `verse`, `prechorus`, `chorus`, `bridge`, and `final chorus` slots conservatively",
        "- replace scaffold hook lines with grounded hook lines from the source bundle",
        "- remove scaffold language from `source_provenance.notes`, `song_intent.emotional_thesis`, and copyright notes",
        "- keep provenance and narrative role unchanged unless the validated bundle proves a contradiction",
        "",
    ]
    for artist in payload.get("artists", []):
        lines.append(f"## {artist['artist_id']}")
        lines.append("")
        for track in artist.get("tracks", []):
            unresolved = ", ".join(track.get("unresolved_section_slots", [])) or "none"
            lines.append(
                f"- `{track['track_id']}` / unresolved section slots `{unresolved}` / source bundle `{track['source_bundle_path']}` / current record `{track['current_record_path']}`"
            )
        lines.append("")
    return "\n".join(lines)


def write_phase1_reopen_outputs(root: Path | None = None) -> dict[str, Path]:
    root = root or project_root()
    assessment = build_phase1_reopen_assessment(root)
    overview = build_internal_normalization_overview(assessment)

    reports_dir = root / "reports" / "planning"
    workflow_dir = root / "data" / "_global" / "generation_safety_phase1_internal_normalization"
    workflow_dir.mkdir(parents=True, exist_ok=True)

    paths = {
        "assessment_json": write_utf8_json(reports_dir / "generation_safety_phase1_reopen_assessment.json", assessment),
        "assessment_md": write_utf8_text(
            reports_dir / "generation_safety_phase1_reopen_assessment.md",
            render_phase1_reopen_markdown(assessment),
            trailing_newline=False,
        ),
        "overview_json": write_utf8_json(workflow_dir / "overview.json", overview),
        "overview_md": write_utf8_text(
            workflow_dir / "overview.md",
            render_internal_normalization_overview_markdown(overview),
            trailing_newline=False,
        ),
    }

    for artist in overview.get("artists", []):
        artist_dir = workflow_dir / artist["artist_id"]
        artist_dir.mkdir(parents=True, exist_ok=True)
        packet = {
            "schema_version": "1.0",
            "record_type": "generation_safety_phase1_internal_normalization_packet",
            "artist_id": artist["artist_id"],
            "track_count": artist["track_count"],
            "tracks": artist["tracks"],
        }
        packet_md_lines = [
            f"# {artist['artist_id']} Phase1 Internal Normalization Packet",
            "",
            f"- tracks: `{artist['track_count']}`",
            "",
        ]
        for track in artist["tracks"]:
            unresolved = ", ".join(track.get("unresolved_section_slots", [])) or "none"
            packet_md_lines.extend(
                [
                    f"## {track['track_id']}",
                    "",
                    f"- current record: `{track['current_record_path']}`",
                    f"- source bundle: `{track['source_bundle_path']}`",
                    f"- current sections: `{', '.join(track.get('current_section_names', []))}`",
                    f"- bundle sections: `{', '.join(track.get('bundle_section_names', []))}`",
                    f"- unresolved section slots: `{unresolved}`",
                    "",
                ]
            )
        paths[f"{artist['artist_id']}_packet_json"] = write_utf8_json(artist_dir / "packet.json", packet)
        paths[f"{artist['artist_id']}_packet_md"] = write_utf8_text(
            artist_dir / "packet.md",
            "\n".join(packet_md_lines).rstrip(),
            trailing_newline=False,
        )

    return paths
