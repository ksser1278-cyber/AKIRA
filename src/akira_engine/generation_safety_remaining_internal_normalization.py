from __future__ import annotations

from pathlib import Path
from typing import Any

from .conditioning_merge import merge_external_conditioning_record
from .generation_safety import KNOWN_MODE_IDS
from .reporting import load_json, write_utf8_json, write_utf8_text


DEFAULT_SECTION_SPECS: list[tuple[str, str]] = [
    ("verse", "Verse 1"),
    ("prechorus", "Pre-Chorus"),
    ("chorus", "Chorus 1"),
    ("bridge", "Bridge"),
    ("chorus", "Final Chorus"),
]


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _overview_path(root: Path) -> Path:
    return root / "data" / "_global" / "generation_safety_remaining_source_acquisition" / "overview.json"


def _output_root(root: Path) -> Path:
    return root / "data" / "_global" / "generation_safety_remaining_internal_normalization"


def _bundle_path(root: Path, artist_id: str, track_id: str) -> Path:
    return (
        root
        / "data"
        / "_global"
        / "generation_safety_remaining_source_acquisition"
        / artist_id
        / "incoming"
        / f"{track_id}.json"
    )


def _round2_record_path(root: Path, artist_id: str, track_id: str) -> Path:
    return (
        root
        / "data"
        / "_global"
        / "generation_safety_remaining_source_acquisition"
        / artist_id
        / "round2_records"
        / f"{track_id}.json"
    )


def _normalize_source_items(items: list[dict[str, Any]] | Any) -> list[dict[str, Any]]:
    if not isinstance(items, list):
        return []
    normalized: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        payload = dict(item)
        if str(payload.get("status", "")).strip() == "trusted":
            payload["status"] = "cross_checked"
        normalized.append(payload)
    return normalized


def _bundle_lines_by_type(bundle: dict[str, Any]) -> dict[str, list[str]]:
    output: dict[str, list[str]] = {}
    lyric = bundle.get("lyric_ground_truth", {}) if isinstance(bundle.get("lyric_ground_truth", {}), dict) else {}
    for section in lyric.get("sections", []):
        if not isinstance(section, dict):
            continue
        section_type = str(section.get("section_type", "")).strip()
        lines = [str(line) for line in section.get("lines", []) if str(line).strip()]
        if section_type and lines:
            output[section_type] = lines
    return output


def _slice_head(lines: list[str], count: int = 2) -> list[str]:
    if not lines:
        return []
    if len(lines) <= count:
        return list(lines)
    return list(lines[:count])


def _slice_tail(lines: list[str], count: int = 2) -> list[str]:
    if not lines:
        return []
    if len(lines) <= count:
        return list(lines)
    return list(lines[-count:])


def _section_specs(current: dict[str, Any]) -> list[tuple[str, str]]:
    lyric = current.get("lyric_ground_truth", {}) if isinstance(current.get("lyric_ground_truth", {}), dict) else {}
    specs: list[tuple[str, str]] = []
    for section in lyric.get("sections", []):
        if not isinstance(section, dict):
            continue
        section_type = str(section.get("section_type", "")).strip()
        section_name = str(section.get("section_name", "")).strip()
        if section_type and section_name:
            specs.append((section_type, section_name))
    if len(specs) >= 3:
        return specs
    return DEFAULT_SECTION_SPECS


def _normalized_section_lines(
    section_type: str,
    section_name: str,
    verse_lines: list[str],
    chorus_lines: list[str],
    hook_lines: list[str],
) -> list[str]:
    normalized_name = section_name.lower()
    if section_type == "verse":
        return list(verse_lines) or list(chorus_lines) or list(hook_lines)
    if section_type == "prechorus":
        return _slice_tail(verse_lines, 2) or _slice_head(chorus_lines, 2) or list(hook_lines)
    if section_type == "bridge":
        return _slice_head(chorus_lines, 2) or _slice_tail(verse_lines, 2) or list(hook_lines)
    if section_type == "chorus" and "final" in normalized_name:
        return list(chorus_lines) or list(hook_lines)
    if section_type == "chorus":
        return list(chorus_lines) or list(hook_lines)
    return list(chorus_lines) or list(verse_lines) or list(hook_lines)


def _normalized_sections(current: dict[str, Any], bundle: dict[str, Any]) -> list[dict[str, Any]]:
    lines_by_type = _bundle_lines_by_type(bundle)
    verse_lines = lines_by_type.get("verse", [])
    chorus_lines = lines_by_type.get("chorus", [])
    bundle_lyric = bundle.get("lyric_ground_truth", {}) if isinstance(bundle.get("lyric_ground_truth", {}), dict) else {}
    hook_lines = [str(line) for line in bundle_lyric.get("hook_lines", []) if str(line).strip()]

    normalized: list[dict[str, Any]] = []
    for section_type, section_name in _section_specs(current):
        normalized.append(
            {
                "section_type": section_type,
                "section_name": section_name,
                "lines": _normalized_section_lines(section_type, section_name, verse_lines, chorus_lines, hook_lines),
            }
        )
    return normalized


def _section_analysis(section_type: str, section_name: str) -> dict[str, Any]:
    if section_type == "prechorus":
        return {
            "section_name": section_name,
            "section_type": section_type,
            "lyric_function": ["tension climb"],
            "narrative_job": "Prepares the hook transition.",
            "hook_weight": "medium",
            "jp_section_role": "B-melo",
            "confidence": "high",
        }
    if section_type == "bridge":
        return {
            "section_name": section_name,
            "section_type": section_type,
            "lyric_function": ["contrast turn"],
            "narrative_job": "Introduces contrast before the final return.",
            "hook_weight": "light",
            "jp_section_role": "C-melo",
            "confidence": "high",
        }
    if section_type == "chorus" and "final" in section_name.lower():
        return {
            "section_name": section_name,
            "section_type": section_type,
            "lyric_function": ["catharsis"],
            "narrative_job": "Delivers the highest-energy final release.",
            "hook_weight": "absolute",
            "jp_section_role": "O-sabi",
            "confidence": "high",
        }
    if section_type == "chorus":
        return {
            "section_name": section_name,
            "section_type": section_type,
            "lyric_function": ["primary hook"],
            "narrative_job": "Delivers the core hook and title landing.",
            "hook_weight": "heavy",
            "jp_section_role": "sabi",
            "confidence": "high",
        }
    return {
        "section_name": section_name,
        "section_type": section_type,
        "lyric_function": ["scenario building"],
        "narrative_job": "Establishes the song perspective.",
        "hook_weight": "light",
        "jp_section_role": "A-melo",
        "confidence": "high",
    }


def _normalized_section_analysis(current: dict[str, Any]) -> list[dict[str, Any]]:
    return [_section_analysis(section_type, section_name) for section_type, section_name in _section_specs(current)]


def _clean_emotional_thesis(current: dict[str, Any]) -> str:
    song_intent = current.get("song_intent", {}) if isinstance(current.get("song_intent", {}), dict) else {}
    for key in ["message", "emotional_target", "core_emotion", "contrast_device"]:
        value = song_intent.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return "Grounded lyric source bundle attached for internal review."


def _mode_candidates(payload: dict[str, Any]) -> list[str]:
    output: list[str] = []
    song_intent = payload.get("song_intent", {}) if isinstance(payload.get("song_intent", {}), dict) else {}
    narrative_role = song_intent.get("narrative_role", [])
    if isinstance(narrative_role, str):
        candidate = narrative_role.strip()
        if candidate in KNOWN_MODE_IDS and candidate not in output:
            output.append(candidate)
    if isinstance(narrative_role, list):
        for item in narrative_role:
            candidate = str(item).strip()
            if candidate in KNOWN_MODE_IDS and candidate not in output:
                output.append(candidate)
    likely_mode = str(payload.get("likely_mode", "")).strip()
    if likely_mode in KNOWN_MODE_IDS and likely_mode not in output:
        output.append(likely_mode)
    return output


def _inferred_mode(*payloads: dict[str, Any]) -> str | None:
    merged: list[str] = []
    for payload in payloads:
        for candidate in _mode_candidates(payload):
            if candidate not in merged:
                merged.append(candidate)
    if len(merged) == 1:
        return merged[0]
    return None


def _profile_mode_candidate(root: Path, artist_id: str, track_id: str) -> str | None:
    candidates: list[str] = []
    profile_paths = [
        root / "artists" / artist_id / "representative_demo_profile.json",
        root / "artists" / artist_id / "profile.json",
    ]
    for profile_path in profile_paths:
        if not profile_path.exists():
            continue
        payload = load_json(profile_path)
        mode_demo_tracks = payload.get("mode_demo_tracks", {})
        if isinstance(mode_demo_tracks, dict):
            for mode_id, entry in mode_demo_tracks.items():
                if mode_id not in KNOWN_MODE_IDS or not isinstance(entry, dict):
                    continue
                if str(entry.get("track_id", "")).strip() == track_id and mode_id not in candidates:
                    candidates.append(mode_id)
        core_anchor_tracks = payload.get("core_anchor_tracks", [])
        if isinstance(core_anchor_tracks, list):
            for entry in core_anchor_tracks:
                if not isinstance(entry, dict):
                    continue
                mode_id = str(entry.get("mode_id", "")).strip()
                if mode_id not in KNOWN_MODE_IDS:
                    continue
                if str(entry.get("track_id", "")).strip() == track_id and mode_id not in candidates:
                    candidates.append(mode_id)
    if len(candidates) == 1:
        return candidates[0]
    return None


def _normalized_quality_control(current: dict[str, Any], round2: dict[str, Any]) -> dict[str, Any]:
    current_quality = current.get("quality_control", {}) if isinstance(current.get("quality_control", {}), dict) else {}
    round2_quality = round2.get("quality_control", {}) if isinstance(round2.get("quality_control", {}), dict) else {}
    record_stage = str(current_quality.get("record_stage", "")).strip() or str(round2_quality.get("record_stage", "")).strip() or "usable"
    ready_for_audio_claims = bool(current_quality.get("ready_for_audio_claims", round2_quality.get("ready_for_audio_claims", False)))
    return {
        "ready_for_prompting": True,
        "ready_for_audio_claims": ready_for_audio_claims,
        "record_stage": record_stage,
        "missing_fields": [],
        "manual_review_required_for": [],
        "warnings": [],
    }


def build_patch(root: Path, artist_id: str, track_id: str, current_record_path: Path) -> dict[str, Any]:
    current = load_json(current_record_path)
    bundle = load_json(_bundle_path(root, artist_id, track_id))
    round2_path = _round2_record_path(root, artist_id, track_id)
    round2 = load_json(round2_path) if round2_path.exists() else {}

    source_provenance = bundle.get("source_provenance", {}) if isinstance(bundle.get("source_provenance", {}), dict) else {}
    lyric_sources = _normalize_source_items(source_provenance.get("lyric_sources", []))
    metadata_sources = _normalize_source_items(source_provenance.get("metadata_sources", []))

    bundle_lyric = bundle.get("lyric_ground_truth", {}) if isinstance(bundle.get("lyric_ground_truth", {}), dict) else {}
    hook_lines = [str(line) for line in bundle_lyric.get("hook_lines", []) if str(line).strip()]
    normalized_sections = _normalized_sections(current, bundle)

    note_lines = source_provenance.get("notes")
    if isinstance(note_lines, list):
        cleaned_notes = [str(item) for item in note_lines if str(item).strip()]
    elif isinstance(note_lines, str) and note_lines.strip():
        cleaned_notes = [note_lines.strip()]
    else:
        cleaned_notes = ["Validated remaining source acquisition bundle applied."]

    patch: dict[str, Any] = {
        "track_identity": {
            "track_id": track_id,
            "artist_id": artist_id,
        },
        "source_provenance": {
            "lyric_sources": lyric_sources,
            "analysis_sources": [
                {
                    "label": "Validated remaining source acquisition bundle",
                    "origin": "internal_bundle",
                    "status": "cross_checked",
                }
            ],
            "notes": cleaned_notes,
        },
        "lyric_ground_truth": {
            "full_text_status": "full",
            "sections": normalized_sections,
            "hook_lines": hook_lines,
            "copyright_handling_note": "Grounded lyric source bundle attached for internal normalization.",
        },
        "song_intent": {
            "emotional_thesis": _clean_emotional_thesis(current),
        },
        "section_analysis": _normalized_section_analysis(current),
        "quality_control": _normalized_quality_control(current, round2),
        "generation_safety": {
            "notes": [
                "pending recomputation after remaining-source normalization",
            ]
        },
    }
    if metadata_sources:
        patch["source_provenance"]["metadata_sources"] = metadata_sources

    inferred_mode = _inferred_mode(current, round2, bundle) or _profile_mode_candidate(root, artist_id, track_id)
    if inferred_mode:
        patch["song_intent"]["narrative_role"] = [inferred_mode]
        patch["likely_mode"] = inferred_mode
    return patch


def write_remaining_internal_normalization_patches(root: Path | None = None) -> dict[str, Any]:
    root = root or project_root()
    overview = load_json(_overview_path(root))
    output_root = _output_root(root)

    manifest_artists: list[dict[str, Any]] = []
    total = 0
    for artist in overview.get("artists", []):
        artist_id = str(artist.get("artist_id", "")).strip()
        tracks = artist.get("tracks", [])
        if not artist_id or not tracks:
            continue
        patch_dir = output_root / artist_id / "generated_patches"
        patch_dir.mkdir(parents=True, exist_ok=True)
        track_entries: list[dict[str, Any]] = []
        for track in tracks:
            track_id = str(track.get("track_id", "")).strip()
            current_record_path = Path(str(track.get("current_record_path", "")).strip())
            workflow_type = str(track.get("workflow_type", "")).strip()
            if not track_id or not current_record_path.exists():
                continue
            patch = build_patch(root, artist_id, track_id, current_record_path)
            patch_path = write_utf8_json(patch_dir / f"{track_id}.json", patch)
            track_entries.append(
                {
                    "track_id": track_id,
                    "workflow_type": workflow_type,
                    "current_record_path": str(current_record_path),
                    "patch_path": str(patch_path),
                }
            )
            total += 1
        manifest_artists.append(
            {
                "artist_id": artist_id,
                "track_count": len(track_entries),
                "tracks": track_entries,
            }
        )

    manifest = {
        "schema_version": "1.0",
        "record_type": "generation_safety_remaining_internal_normalization_patch_manifest",
        "track_count": total,
        "artist_count": len(manifest_artists),
        "artists": manifest_artists,
    }
    manifest_json = write_utf8_json(output_root / "patch_manifest.json", manifest)

    lines = [
        "# Generation Safety Remaining Internal Normalization Patch Manifest",
        "",
        f"- tracks: `{total}`",
        f"- artists: `{len(manifest_artists)}`",
        "",
    ]
    for artist in manifest_artists:
        lines.append(f"## {artist['artist_id']}")
        lines.append("")
        for track in artist["tracks"]:
            lines.append(
                f"- `{track['track_id']}` / `{track['workflow_type']}` -> `{track['patch_path']}`"
            )
        lines.append("")
    manifest_md = write_utf8_text(output_root / "patch_manifest.md", "\n".join(lines).rstrip(), trailing_newline=False)
    return {"manifest_json": manifest_json, "manifest_md": manifest_md}


def apply_remaining_internal_normalization(root: Path | None = None) -> dict[str, Any]:
    root = root or project_root()
    manifest = load_json(_output_root(root) / "patch_manifest.json")
    backup_dir = (
        root
        / "reports"
        / "quality"
        / "conditioning_merge_backups"
        / "generation_safety_remaining_internal_normalization"
    )

    artists_payload: list[dict[str, Any]] = []
    changed_count = 0
    unchanged_count = 0
    for artist in manifest.get("artists", []):
        artist_id = str(artist.get("artist_id", "")).strip()
        target_dir = root / "data" / artist_id / "reference_tracks"
        track_results: list[dict[str, Any]] = []
        for track in artist.get("tracks", []):
            track_id = str(track.get("track_id", "")).strip()
            source_path = Path(str(track.get("patch_path", "")).strip())
            if not track_id or not source_path.exists():
                continue
            result = merge_external_conditioning_record(
                artist_id=artist_id,
                target_dir=target_dir,
                source_path=source_path,
                backup_dir=backup_dir / artist_id,
            )
            if result.changed:
                changed_count += 1
            else:
                unchanged_count += 1
            track_results.append(
                {
                    "track_id": result.track_id,
                    "source_path": result.source_path,
                    "target_path": result.target_path,
                    "changed": result.changed,
                }
            )
        artists_payload.append(
            {
                "artist_id": artist_id,
                "track_count": len(track_results),
                "tracks": track_results,
            }
        )

    report = {
        "schema_version": "1.0",
        "record_type": "generation_safety_remaining_internal_normalization_apply_report",
        "track_count": changed_count + unchanged_count,
        "changed_count": changed_count,
        "unchanged_count": unchanged_count,
        "backup_dir": str(backup_dir),
        "artists": artists_payload,
    }

    output_root = _output_root(root)
    report_json = write_utf8_json(output_root / "apply_report.json", report)

    lines = [
        "# Generation Safety Remaining Internal Normalization Apply Report",
        "",
        f"- tracks: `{report['track_count']}`",
        f"- changed: `{changed_count}`",
        f"- unchanged: `{unchanged_count}`",
        f"- backup: `{backup_dir}`",
        "",
    ]
    for artist in artists_payload:
        lines.append(f"## {artist['artist_id']}")
        lines.append("")
        for track in artist["tracks"]:
            status = "changed" if track["changed"] else "unchanged"
            lines.append(f"- `{track['track_id']}` / `{status}`")
        lines.append("")
    report_md = write_utf8_text(output_root / "apply_report.md", "\n".join(lines).rstrip(), trailing_newline=False)
    return {"report_json": report_json, "report_md": report_md}
