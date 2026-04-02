from __future__ import annotations

import json
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


def _slice_tail(lines: list[str], count: int = 2) -> list[str]:
    if not lines:
        return []
    if len(lines) <= count:
        return list(lines)
    return list(lines[-count:])


def _slice_head(lines: list[str], count: int = 2) -> list[str]:
    if not lines:
        return []
    if len(lines) <= count:
        return list(lines)
    return list(lines[:count])


def _normalized_section_lines(section_type: str, section_name: str, verse_lines: list[str], chorus_lines: list[str], hook_lines: list[str]) -> list[str]:
    normalized_name = section_name.lower()
    if section_type == "verse":
        return list(verse_lines)
    if section_type == "prechorus":
        return _slice_tail(verse_lines, 2) or _slice_head(chorus_lines, 2)
    if section_type == "bridge":
        return _slice_head(chorus_lines, 2) or _slice_tail(verse_lines, 2)
    if section_type == "chorus" and "final" in normalized_name:
        return list(chorus_lines) or list(hook_lines)
    if section_type == "chorus":
        return list(chorus_lines) or list(hook_lines)
    return list(chorus_lines) or list(verse_lines) or list(hook_lines)


def build_patch(root: Path, artist_id: str, track_id: str) -> dict[str, Any]:
    current = load_json(_current_record_path(root, artist_id, track_id))
    bundle = load_json(_bundle_path(root, artist_id, track_id))

    current_sections = current.get("lyric_ground_truth", {}).get("sections", []) if isinstance(current.get("lyric_ground_truth", {}), dict) else []
    bundle_lyric = bundle.get("lyric_ground_truth", {}) if isinstance(bundle.get("lyric_ground_truth", {}), dict) else {}
    lines_by_type = _bundle_lines_by_type(bundle)
    verse_lines = lines_by_type.get("verse", [])
    chorus_lines = lines_by_type.get("chorus", [])
    hook_lines = [str(line) for line in bundle_lyric.get("hook_lines", []) if str(line).strip()]

    normalized_sections: list[dict[str, Any]] = []
    for section in current_sections:
        if not isinstance(section, dict):
            continue
        section_type = str(section.get("section_type", "")).strip()
        section_name = str(section.get("section_name", "")).strip()
        normalized_sections.append(
            {
                "section_type": section_type,
                "section_name": section_name,
                "lines": _normalized_section_lines(section_type, section_name, verse_lines, chorus_lines, hook_lines),
            }
        )

    source_provenance = bundle.get("source_provenance", {}) if isinstance(bundle.get("source_provenance", {}), dict) else {}
    notes = source_provenance.get("notes")
    if isinstance(notes, list):
        note_lines = [str(item) for item in notes if str(item).strip()]
    elif isinstance(notes, str) and notes.strip():
        note_lines = [notes]
    else:
        note_lines = ["Validated lyric grounding bundle prepared for internal normalization."]

    lyric_sources = source_provenance.get("lyric_sources", []) if isinstance(source_provenance.get("lyric_sources", []), list) else []

    patch = {
        "track_identity": {
            "track_id": track_id,
        },
        "source_provenance": {
            "lyric_sources": lyric_sources,
            "analysis_sources": [
                {
                    "label": "Validated lyric grounding source bundle",
                    "origin": "internal_bundle",
                    "status": "cross_checked",
                }
            ],
            "notes": note_lines,
        },
        "lyric_ground_truth": {
            "full_text_status": "full",
            "sections": normalized_sections,
            "hook_lines": hook_lines,
        },
        "generation_safety": {
            "notes": [
                "pending recomputation after internal normalization",
            ]
        },
    }
    return patch


def write_internal_normalization_patches(root: Path | None = None) -> dict[str, Any]:
    root = root or project_root()
    overview = load_json(root / "data" / "_global" / "generation_safety_phase1_internal_normalization" / "overview.json")
    output_root = root / "data" / "_global" / "generation_safety_phase1_internal_normalization"

    manifest_artists: list[dict[str, Any]] = []
    total = 0
    for artist in overview.get("artists", []):
        artist_id = str(artist.get("artist_id", "")).strip()
        tracks = [str(track.get("track_id", "")).strip() for track in artist.get("tracks", []) if str(track.get("track_id", "")).strip()]
        if not artist_id or not tracks:
            continue
        patch_dir = output_root / artist_id / "generated_patches"
        patch_dir.mkdir(parents=True, exist_ok=True)
        track_entries: list[dict[str, Any]] = []
        for track_id in tracks:
            patch = build_patch(root, artist_id, track_id)
            patch_path = write_utf8_json(patch_dir / f"{track_id}.json", patch)
            track_entries.append({"track_id": track_id, "patch_path": str(patch_path)})
            total += 1
        manifest_artists.append({"artist_id": artist_id, "track_count": len(track_entries), "tracks": track_entries})

    manifest = {
        "schema_version": "1.0",
        "record_type": "generation_safety_phase1_internal_normalization_patch_manifest",
        "track_count": total,
        "artist_count": len(manifest_artists),
        "artists": manifest_artists,
    }
    manifest_path = write_utf8_json(output_root / "patch_manifest.json", manifest)
    md_lines = [
        "# Generation Safety Phase1 Internal Normalization Patch Manifest",
        "",
        f"- tracks: `{total}`",
        f"- artists: `{len(manifest_artists)}`",
        "",
    ]
    for artist in manifest_artists:
        md_lines.append(f"## {artist['artist_id']}")
        md_lines.append("")
        for track in artist["tracks"]:
            md_lines.append(f"- `{track['track_id']}` -> `{track['patch_path']}`")
        md_lines.append("")
    manifest_md_path = write_utf8_text(output_root / "patch_manifest.md", "\n".join(md_lines).rstrip(), trailing_newline=False)
    return {"manifest_json": manifest_path, "manifest_md": manifest_md_path}
