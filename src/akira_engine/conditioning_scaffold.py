from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_audio_seed_conditioning(track: dict[str, Any]) -> dict[str, Any]:
    title = track["title"]
    source_filename = track["source_filename"]
    seconds = int(round(track.get("duration_seconds", 0) or 0))
    minutes = seconds // 60
    remainder = seconds % 60
    display = f"{minutes}:{remainder:02d}" if seconds else ""

    mode = "direct_emotional_pop"
    if any(token in track["track_id"] for token in ("ghost_rule", "tsumi_to_batsu")):
        mode = "dark_cute_breakdown"

    return {
        "schema_version": "1.0",
        "record_type": "track_conditioning_record",
        "track_identity": {
            "track_id": track["track_id"],
            "artist_id": track["artist_id"],
            "artist_name": "DECO*27" if track["artist_id"] == "deco27" else track["artist_id"],
            "title": title,
            "title_core": title.replace(" (Feat. Hatsune Miku)", ""),
            "language": "ja",
            "tie_in": {"has_tie_in": False, "status": "unknown", "sources": []},
            "credits": {
                "vocal": [],
                "lyrics": [],
                "composition": [],
                "arrangement": [],
                "performance": [],
                "mix_master": [],
            },
            "release": {
                "date": {
                    "value": "2023-01-26",
                    "status": "confirmed",
                    "sources": [{"label": "Local owned audio file metadata", "origin": "other", "notes": "DATE tag from FLAC file"}],
                },
                "year": {
                    "value": 2023,
                    "status": "confirmed",
                    "sources": [{"label": "Local owned audio file metadata", "origin": "other", "notes": "DATE tag from FLAC file"}],
                },
                "runtime": {
                    "display": display,
                    "seconds": seconds,
                    "status": "confirmed",
                    "sources": [{"label": "Local owned audio file probe", "origin": "other", "notes": source_filename}],
                },
            },
        },
        "source_provenance": {
            "lyric_sources": [],
            "metadata_sources": [{"label": "Local owned audio file metadata", "origin": "other", "notes": "FLAC tags from Melon library file"}],
            "analysis_sources": [{"label": "AKIRA audio-seeded scaffold", "origin": "manual_note", "accessed_on": "2026-03-21"}],
            "notes": ["Draft scaffold created from owned audio availability. Attach lyric and credit grounding before benchmark use."],
        },
        "lyric_ground_truth": {
            "full_text_status": "partial",
            "copyright_handling_note": "No lyric grounding attached yet. Placeholder sections exist only to keep the record structurally valid until lyric evidence is added.",
            "sections": [
                {
                    "section_type": "verse",
                    "section_name": "Verse",
                    "jp_section_role": "a_melo",
                    "mora_density": "unknown",
                    "spoken_speed_bias": "medium",
                    "title_drop_role": "none",
                    "phrase_energy_role": "observation",
                    "source_labels": ["pending_lyric_grounding"],
                    "lines": [],
                },
                {
                    "section_type": "pre_chorus",
                    "section_name": "Pre-Chorus",
                    "jp_section_role": "b_melo",
                    "mora_density": "unknown",
                    "spoken_speed_bias": "medium",
                    "title_drop_role": "none",
                    "phrase_energy_role": "compression",
                    "source_labels": ["pending_lyric_grounding"],
                    "lines": [],
                },
                {
                    "section_type": "chorus",
                    "section_name": "Chorus",
                    "jp_section_role": "sabi",
                    "mora_density": "unknown",
                    "spoken_speed_bias": "medium",
                    "title_drop_role": "full",
                    "phrase_energy_role": "release",
                    "source_labels": ["pending_lyric_grounding"],
                    "lines": [],
                },
            ],
            "hook_lines": [],
            "question_lines": [],
            "repetition_patterns": [],
        },
        "song_intent": {
            "core_theme": [title.lower()],
            "emotional_thesis": "Draft intent only. Replace with lyric-grounded analysis.",
            "contrast_device": ["pending lyric grounding"],
            "dramatic_arc": ["pending"],
            "narrative_role": [mode],
            "tie_in_function": "",
            "title_function": "Provisional title interpretation only. Replace after lyric grounding.",
            "key_motifs": [title.lower()],
            "interpretation_confidence": "low",
        },
        "audio_fact_layer": {
            "reported_facts": {
                "audio_file_probe": {
                    "format_name": track.get("format_name"),
                    "codec_name": track.get("codec_name"),
                    "sample_rate_hz": track.get("sample_rate_hz"),
                    "channels": track.get("channels"),
                    "channel_layout": track.get("channel_layout"),
                    "bit_rate": track.get("bit_rate"),
                    "status": "confirmed",
                    "sources": [{"label": "Local owned audio file probe", "origin": "other", "notes": source_filename}],
                },
                "measured_audio_profile": {
                    "integrated_lufs": track.get("loudness", {}).get("integrated_lufs"),
                    "lra_lu": track.get("loudness", {}).get("lra_lu"),
                    "rms_median_db": track.get("dynamics", {}).get("rms_median_db"),
                    "rms_span_db": track.get("dynamics", {}).get("rms_span_db"),
                    "early_rms_db": track.get("energy_curve", {}).get("early_rms_db"),
                    "mid_rms_db": track.get("energy_curve", {}).get("mid_rms_db"),
                    "late_rms_db": track.get("energy_curve", {}).get("late_rms_db"),
                    "late_minus_early_db": track.get("energy_curve", {}).get("late_minus_early_db"),
                    "peak_zone": track.get("energy_curve", {}).get("peak_zone"),
                    "status": "confirmed",
                    "sources": [{"label": "Local owned audio file analysis", "origin": "other", "notes": source_filename}],
                },
                "confirmed_instrumentation": [],
            },
            "proxy_inference": {
                "energy_profile": [_energy_label(track)],
                "vocal_behavior": ["pending"],
                "production_palette": ["pending"],
                "arrangement_arc": [f"measured peak zone: {track.get('energy_curve', {}).get('peak_zone')}"] if track.get("energy_curve", {}).get("peak_zone") else [],
                "dynamics_arc": [_dynamics_label(track)],
                "confidence": "low",
                "evidence_basis": ["other"],
            },
            "do_not_overclaim": ["Do not assert exact instrumentation or vocal behavior until lyric grounding and listening notes are added."],
        },
        "section_analysis": [
            _section_stub("Verse", "verse", "a_melo", "observation"),
            _section_stub("Pre-Chorus", "pre_chorus", "b_melo", "compression"),
            _section_stub("Chorus", "chorus", "sabi", "release"),
        ],
        "japanese_lyric_profile": {
            "workflow_bias": "hybrid",
            "hook_copy_force": "unknown",
            "title_ignition_style": "unknown",
            "modern_compression_bias": "medium",
            "phrase_source_types": ["pending lyric grounding"],
            "mora_control_notes": [],
            "accent_risk_notes": [],
            "critic_focus": ["attach lyric evidence before trusting benchmark conclusions"],
            "section_features": [
                {"section_name": "Verse", "section_type": "verse", "jp_section_role": "a_melo", "mora_density": "unknown", "spoken_speed_bias": "medium", "title_drop_role": "none", "phrase_energy_role": "observation"},
                {"section_name": "Pre-Chorus", "section_type": "pre_chorus", "jp_section_role": "b_melo", "mora_density": "unknown", "spoken_speed_bias": "medium", "title_drop_role": "none", "phrase_energy_role": "compression"},
                {"section_name": "Chorus", "section_type": "chorus", "jp_section_role": "sabi", "mora_density": "unknown", "spoken_speed_bias": "medium", "title_drop_role": "full", "phrase_energy_role": "release"},
            ],
        },
        "prompt_conditioning": {
            "genre_anchors": [mode],
            "tempo_feels": ["pending"],
            "vocal_tones": ["pending"],
            "production_palette": ["pending"],
            "energy_arc": [_dynamics_label(track)],
            "imagery_anchors": [title.lower()],
            "exclude": ["do not overclaim arrangement details before lyric/audio grounding is complete"],
            "source_basis": ["other"],
        },
        "quality_control": {
            "missing_fields": ["lyrics", "credits", "hook lines", "section map", "prompt conditioning detail"],
            "manual_review_required_for": ["full lyric grounding", "credit verification", "exact instrumentation claims"],
            "warnings": ["Draft scaffold built from owned audio metadata and measured audio profile."],
            "ready_for_prompting": False,
            "ready_for_audio_claims": False,
        },
    }


def _section_stub(name: str, section_type: str, jp_role: str, energy_role: str) -> dict[str, Any]:
    return {
        "section_name": name,
        "section_type": section_type,
        "source_section_labels": ["pending_lyric_grounding"],
        "lyric_function": ["pending"],
        "narrative_job": "Pending lyric grounding.",
        "arrangement_role": {"summary": "Pending lyric and listening-based review.", "status": "unknown", "evidence_basis": ["other"]},
        "harmony_melody_role": {"summary": "Pending lyric and listening-based review.", "status": "unknown", "evidence_basis": ["other"]},
        "dynamics_role": {"summary": "Pending lyric grounding.", "status": "unknown", "evidence_basis": ["other"]},
        "rhetorical_pattern": [],
        "vocabulary_focus": [],
        "rhyme_features": [],
        "rhythm_features": [],
        "hook_weight": "heavy" if section_type == "chorus" else ("medium" if section_type == "pre_chorus" else "light"),
        "jp_section_role": jp_role,
        "mora_density": "unknown",
        "spoken_speed_bias": "medium",
        "title_drop_role": "full" if section_type == "chorus" else "none",
        "phrase_energy_role": energy_role,
        "confidence": "low",
    }


def _energy_label(track: dict[str, Any]) -> str:
    lift = track.get("energy_curve", {}).get("late_minus_early_db")
    if lift is None:
        return "pending"
    if lift >= 2.0:
        return "strong late lift"
    if lift <= 0.3:
        return "stable compressed pop energy"
    return "moderate late lift"


def _dynamics_label(track: dict[str, Any]) -> str:
    lift = track.get("energy_curve", {}).get("late_minus_early_db")
    if lift is None:
        return "pending"
    if lift >= 2.0:
        return "measured late energy lift"
    return "measured stable end energy"


def scaffold_from_audio_summary(project_root: Path, artist_id: str, track_ids: list[str]) -> list[Path]:
    summary = load_json(project_root / "reports" / "audio" / "audio_analysis_summary.json")
    by_track_id = {track["track_id"]: track for track in summary.get("tracks", [])}
    output_dir = project_root / "data" / artist_id / "reference_tracks"
    created: list[Path] = []
    for track_id in track_ids:
        track = by_track_id.get(track_id)
        if not track:
            continue
        path = output_dir / f"{track_id.removeprefix(artist_id + '_')}.conditioning.json"
        if path.exists():
            continue
        payload = build_audio_seed_conditioning(track)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        created.append(path)
    return created
