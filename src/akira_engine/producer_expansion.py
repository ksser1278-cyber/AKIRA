from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sync_producer_expansion_set(project_root: Path) -> dict[str, Any]:
    gold_anchor = load_json(project_root / "data" / "anchor_sets" / "gold_anchor_set.json")
    producer_expansion = load_json(project_root / "data" / "anchor_sets" / "producer_expansion_set.json")

    gold_by_artist = {
        block["artist_id"]: set(block.get("track_ids", []))
        for block in gold_anchor.get("artists", [])
    }

    results: list[dict[str, Any]] = []
    for artist_block in producer_expansion.get("artists", []):
        artist_id = str(artist_block.get("artist_id", "")).strip()
        current_ids = [str(track_id).strip() for track_id in artist_block.get("track_ids", []) if str(track_id).strip()]
        filtered_ids = [track_id for track_id in current_ids if track_id not in gold_by_artist.get(artist_id, set())]
        removed_ids = [track_id for track_id in current_ids if track_id not in filtered_ids]
        artist_block["track_ids"] = filtered_ids
        results.append(
            {
                "artist_id": artist_id,
                "kept_track_ids": filtered_ids,
                "removed_track_ids": removed_ids,
            }
        )

    write_json(project_root / "data" / "anchor_sets" / "producer_expansion_set.json", producer_expansion)
    return {
        "producer_expansion_path": str(project_root / "data" / "anchor_sets" / "producer_expansion_set.json"),
        "artists": results,
    }


def build_generic_conditioning_scaffold(
    *,
    track_id: str,
    artist_id: str,
    artist_name: str,
    title: str,
    romanized: str,
    mode: str,
) -> dict[str, Any]:
    title_core = romanized or title or track_id
    return {
        "schema_version": "1.0",
        "record_type": "track_conditioning_record",
        "track_identity": {
            "track_id": track_id,
            "artist_id": artist_id,
            "artist_name": artist_name,
            "title": title,
            "title_core": title_core,
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
                "date": {"value": "", "status": "unknown", "sources": []},
                "year": {"value": None, "status": "unknown", "sources": []},
                "runtime": {"display": "", "seconds": None, "status": "unknown", "sources": []},
            },
        },
        "source_provenance": {
            "lyric_sources": [],
            "metadata_sources": [],
            "analysis_sources": [
                {
                    "label": "AKIRA generic producer-expansion scaffold",
                    "origin": "manual_note",
                    "accessed_on": "2026-03-21",
                }
            ],
            "notes": ["Scaffold only. Requires lyric grounding, metadata, and section analysis before benchmark use."],
        },
        "lyric_ground_truth": {
            "full_text_status": "partial",
            "copyright_handling_note": "Scaffold only. Replace with full lyric grounding.",
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
            "core_theme": [title_core.lower()],
            "emotional_thesis": "Scaffold only. Replace with lyric-grounded analysis.",
            "contrast_device": ["pending lyric grounding"],
            "dramatic_arc": ["pending"],
            "narrative_role": [mode],
            "tie_in_function": "",
            "title_function": "Provisional title interpretation only.",
            "key_motifs": [title_core.lower()],
            "interpretation_confidence": "low",
        },
        "audio_fact_layer": {
            "reported_facts": {"confirmed_instrumentation": []},
            "proxy_inference": {
                "energy_profile": ["pending"],
                "vocal_behavior": ["pending"],
                "production_palette": ["pending"],
                "arrangement_arc": ["pending"],
                "dynamics_arc": ["pending"],
                "confidence": "low",
                "evidence_basis": [],
            },
            "do_not_overclaim": ["Do not assert audio details until owned audio or listening notes are attached."],
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
            "critic_focus": ["attach lyric grounding before trusting this record"],
            "section_features": [
                {"section_name": "Verse", "section_type": "verse", "jp_section_role": "a_melo", "mora_density": "unknown", "spoken_speed_bias": "medium", "title_drop_role": "none", "phrase_energy_role": "observation"},
                {"section_name": "Pre-Chorus", "section_type": "pre_chorus", "jp_section_role": "b_melo", "mora_density": "unknown", "spoken_speed_bias": "medium", "title_drop_role": "none", "phrase_energy_role": "compression"},
                {"section_name": "Chorus", "section_type": "chorus", "jp_section_role": "sabi", "mora_density": "unknown", "spoken_speed_bias": "medium", "title_drop_role": "full", "phrase_energy_role": "release"},
            ],
        },
        "prompt_conditioning": {
            "genre_anchors": [mode],
            "tempo_feels": [],
            "vocal_tones": [],
            "production_palette": [],
            "energy_arc": [],
            "imagery_anchors": [title_core.lower()],
            "exclude": ["scaffold only; replace with track-grounded prompt conditioning"],
            "source_basis": [],
        },
        "quality_control": {
            "missing_fields": ["lyrics", "credits", "release date", "runtime", "hook lines", "section map", "prompt conditioning detail"],
            "manual_review_required_for": ["full lyric grounding", "credit verification", "audio enrichment"],
            "warnings": ["Generic scaffold only. Not ready for benchmark or prompting."],
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
        "arrangement_role": {"summary": "Pending review.", "status": "unknown", "evidence_basis": []},
        "harmony_melody_role": {"summary": "Pending review.", "status": "unknown", "evidence_basis": []},
        "dynamics_role": {"summary": "Pending review.", "status": "unknown", "evidence_basis": []},
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


def scaffold_from_queue(project_root: Path, artist_id: str) -> list[str]:
    queue_path = project_root / "data" / artist_id / "reference_tracks" / "conditioning_queue.json"
    queue = load_json(queue_path)
    output_dir = project_root / "data" / artist_id / "reference_tracks"
    created: list[str] = []
    for item in queue.get("queue", []):
        if str(item.get("status", "")).strip().lower() != "pending":
            continue
        track_id = str(item.get("track_id", "")).strip()
        if not track_id:
            continue
        file_name = track_id.removeprefix(f"{artist_id}_") + ".conditioning.json"
        target_path = output_dir / file_name
        if target_path.exists():
            continue
        payload = build_generic_conditioning_scaffold(
            track_id=track_id,
            artist_id=artist_id,
            artist_name=str(queue.get("artist_name", artist_id)),
            title=str(item.get("title", "")).strip(),
            romanized=str(item.get("romanized", "")).strip(),
            mode=str(item.get("mode", "")).strip() or "unknown",
        )
        write_json(target_path, payload)
        created.append(str(target_path))
    return created
