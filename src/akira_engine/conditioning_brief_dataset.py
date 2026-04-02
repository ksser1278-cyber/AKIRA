from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def canonical_section(section_type: str, jp_role: str, index_map: dict[str, int]) -> str:
    role = (jp_role or "").strip()
    if role == "a_melo":
        index_map["a_melo"] = index_map.get("a_melo", 0) + 1
        return "verse_1" if index_map["a_melo"] == 1 else "verse_2"
    if role == "b_melo":
        index_map["b_melo"] = index_map.get("b_melo", 0) + 1
        return "pre_chorus" if index_map["b_melo"] == 1 else "pre_chorus_2"
    if role == "sabi":
        index_map["sabi"] = index_map.get("sabi", 0) + 1
        return "chorus" if index_map["sabi"] == 1 else "chorus_final"
    if role == "c_melo":
        index_map["c_melo"] = index_map.get("c_melo", 0) + 1
        return "bridge" if index_map["c_melo"] == 1 else "bridge_rise"
    if role == "intro":
        return "intro"
    if role == "outro":
        return "outro"
    fallback = {
        "verse": "verse_1",
        "pre_chorus": "pre_chorus",
        "chorus": "chorus",
        "bridge": "bridge",
        "intro": "intro",
        "outro": "outro",
    }
    return fallback.get(section_type, section_type or "other")


def unique(values: list[str]) -> list[str]:
    seen = set()
    out = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            out.append(value)
    return out


def load_active_queue_records(reference_dir: Path, artist_id: str) -> list[tuple[Path, str]]:
    queue_path = reference_dir / "conditioning_queue.json"
    if not queue_path.exists():
        return [(path, "ironic_meta") for path in sorted(reference_dir.glob("*.conditioning.json"))]

    queue = json.loads(queue_path.read_text(encoding="utf-8"))
    records: list[tuple[Path, str]] = []
    for item in queue.get("queue", []):
        status = str(item.get("status", "")).strip().lower()
        if status == "pending":
            continue
        track_id = str(item.get("track_id", "")).strip()
        if not track_id:
            continue
        raw_id = track_id.removeprefix(f"{artist_id}_")
        path = reference_dir / f"{raw_id}.conditioning.json"
        if not path.exists():
            continue
        mode = str(item.get("mode", "")).strip() or "ironic_meta"
        records.append((path, mode))
    return records


def conditioning_to_brief(conditioning: dict[str, Any], primary_mode: str, source_path: Path) -> dict[str, Any]:
    identity = conditioning["track_identity"]
    intent = conditioning["song_intent"]
    prompt = conditioning["prompt_conditioning"]
    jp_profile = conditioning.get("japanese_lyric_profile", {})
    sections = conditioning.get("lyric_ground_truth", {}).get("sections", [])
    analysis = conditioning.get("section_analysis", [])

    index_map: dict[str, int] = {}
    ordered_sections = []
    style_tags = []
    if identity["artist_name"] in {"PinocchioP", "DECO*27", "Kanaria", "MARETU", "Kairiki Bear"}:
        style_tags.extend(["Vocaloid", "Subculture"])

    for section in sections:
        inferred = canonical_section(
            str(section.get("section_type", "")),
            str(section.get("jp_section_role", "")),
            index_map,
        )
        ordered_sections.append(
            {
                "source_section": section.get("section_name") or inferred,
                "inferred_label": inferred,
                "line_count": len(section.get("lines", [])),
                "reason": ", ".join(section.get("lines", [])[:1]) or "Derived from conditioning section role.",
            }
        )

    dominant_imagery = list(prompt.get("imagery_anchors", []))[:6]
    dominant_emotions = list(intent.get("core_theme", []))[:3]
    compatible_modes = [primary_mode]
    if primary_mode == "ironic_meta":
        compatible_modes.append("dark_cute_breakdown")

    return {
        "record_id": f"{identity['track_id']}-conditioning-brief",
        "split": "train",
        "task_type": "full_song_brief",
        "artist_id": identity["artist_id"],
        "artist_name": identity["artist_name"],
        "track_id": identity["track_id"],
        "title": identity["title"],
        "contains_copyrighted_lyrics": False,
        "source_paths": {"conditioning_record": str(source_path)},
        "artist_style_card_id": f"{identity['artist_id']}-conditioning-style-card",
        "instruction": f"Produce a complete {identity['artist_name']}-adjacent generation brief from conditioning evidence. Return mode, structure, hook plan, style constraints, and prompt seed.",
        "input_context": {
            "artist_context": {
                "summary": intent.get("emotional_thesis", ""),
                "style_tags": unique(style_tags + [primary_mode, "Hook-Centered", "Copy-Driven"]),
                "imagery_bank": dominant_imagery,
                "core_themes": list(intent.get("core_theme", [])),
                "structural_defaults": [item["inferred_label"] for item in ordered_sections],
            },
            "track_evidence": {
                "observed_section_count": len(ordered_sections),
                "has_pre_chorus": any(item["inferred_label"].startswith("pre_chorus") for item in ordered_sections),
                "has_bridge": any(item["inferred_label"].startswith("bridge") for item in ordered_sections),
                "has_outro": any(item["inferred_label"] == "outro" for item in ordered_sections),
                "inferred_song_form": {
                    "confidence": "medium",
                    "ordered_sections": ordered_sections,
                    "form_labels": [item["inferred_label"] for item in ordered_sections],
                    "chorus_anchor_sections": [
                        item["source_section"] for item in ordered_sections if item["inferred_label"].startswith("chorus")
                    ],
                },
                "dominant_imagery_tags": dominant_imagery,
                "dominant_emotions": dominant_emotions,
                "overall_arc_label": "build_and_release"
                if any(item["inferred_label"].startswith("chorus") for item in ordered_sections)
                else "flat_or_circular",
                "hook_strategy": {
                    "hook_density": "high" if jp_profile.get("hook_copy_force") == "high" else "medium",
                    "hook_candidate_count": len(conditioning.get("lyric_ground_truth", {}).get("hook_lines", [])),
                    "repeated_line_count": len(conditioning.get("lyric_ground_truth", {}).get("hook_lines", [])),
                    "repeated_opening_count": len(conditioning.get("lyric_ground_truth", {}).get("repetition_patterns", [])),
                    "chorus_repetition_score": 0.8 if conditioning.get("lyric_ground_truth", {}).get("hook_lines") else 0.3,
                },
                "language_profile": {
                    "dominant_perspective": "first_person",
                    "english_insertion_level": "low",
                    "line_length_profile": {
                        "average_characters": 12.0,
                        "short_line_ratio": 0.7 if jp_profile.get("modern_compression_bias") == "high" else 0.5,
                    },
                    "script_balance": {
                        "ascii_tokens": 0,
                        "japanese_chunks": sum(len(section.get("lines", [])) for section in sections),
                    },
                },
            },
            "artist_frame": {
                "top_imagery_clusters": dominant_imagery,
                "dominant_arc_patterns": list(intent.get("dramatic_arc", [])),
                "mode_candidates": compatible_modes,
            },
        },
        "target": {
            "primary_mode": primary_mode,
            "theme_axes": unique(list(intent.get("core_theme", [])) + dominant_imagery)[:8],
            "style_constraints": {
                "style_tags": unique(style_tags + [primary_mode, "Hook-Centered", "Copy-Driven", "Vocaloid"]),
                "language_policy": {
                    "primary_language": "Japanese",
                    "allowed_languages": ["Japanese"],
                    "avoid_languages": ["English-heavy lyrics"],
                },
                "imagery_bank": dominant_imagery,
                "avoid_terms": list(prompt.get("exclude", [])),
                "compatible_modes": compatible_modes,
            },
            "track_conditioned_structure": {
                "confidence": "medium",
                "ordered_sections": ordered_sections,
                "form_labels": [item["inferred_label"] for item in ordered_sections],
                "chorus_anchor_sections": [
                    item["source_section"] for item in ordered_sections if item["inferred_label"].startswith("chorus")
                ],
            },
            "recommended_structure": [
                {
                    "section": item["inferred_label"],
                    "goal": next(
                        (
                            entry.get("narrative_job")
                            for entry in analysis
                            if entry.get("section_name") == item["source_section"]
                        ),
                        "Keep the section purposeful and image-driven.",
                    ),
                }
                for item in ordered_sections
            ],
            "hook_plan": {
                "hook_density": "high" if jp_profile.get("hook_copy_force") == "high" else "medium",
                "hook_candidate_count": len(conditioning.get("lyric_ground_truth", {}).get("hook_lines", [])),
                "repeated_line_count": len(conditioning.get("lyric_ground_truth", {}).get("hook_lines", [])),
                "repeated_opening_count": len(conditioning.get("lyric_ground_truth", {}).get("repetition_patterns", [])),
                "chorus_repetition_score": 0.8 if conditioning.get("lyric_ground_truth", {}).get("hook_lines") else 0.3,
            },
            "generation_notes": [
                "Use conditioning motifs and section roles directly.",
                "Keep title-drop behavior aligned with the validated conditioning record.",
                "Do not generalize into broad J-pop sentimentality.",
            ],
            "style_prompt_seed": {
                "style_of_music": ", ".join(prompt.get("genre_anchors", [])[:2]),
                "vocal_direction": list(prompt.get("vocal_tones", [])),
                "lyric_direction": [
                    f"themes: {', '.join(intent.get('core_theme', []))}",
                    f"imagery anchors: {', '.join(dominant_imagery)}",
                ],
                "section_emphasis": [item["inferred_label"] for item in ordered_sections],
            },
        },
    }


def build_briefs_from_conditioning_paths(entries: list[tuple[Path, str]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path, primary_mode in entries:
        with path.open("r", encoding="utf-8") as f:
            conditioning = json.load(f)
        records.append(conditioning_to_brief(conditioning, primary_mode, path))
    return records
