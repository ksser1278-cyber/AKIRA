from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


RECOMMENDATION_ORDER = {
    "blocked": 0,
    "needs_review": 1,
    "ready": 2,
}
BLOCKED_TRACK_ISSUES = {
    "missing_raw_file",
    "empty_raw_text",
    "too_short_text",
    "too_few_lines",
    "missing_normalized_doc",
    "malformed_normalized_doc",
    "too_few_sections",
    "missing_track_analysis",
}
MODE_HINT_MAP = {
    "night": {"night_drive"},
    "city": {"night_drive"},
    "motion": {"night_drive", "anthemic_cinematic"},
    "body": {"intimate_confessional"},
    "fracture": {"rebellious_dark", "intimate_confessional"},
    "fire": {"rebellious_dark", "anthemic_cinematic"},
    "light": {"anthemic_cinematic"},
    "noise": {"rebellious_dark"},
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(record, ensure_ascii=False) for record in records) + ("\n" if records else ""),
        encoding="utf-8",
    )
    return path


def deterministic_split(record_id: str) -> str:
    bucket = int(hashlib.md5(record_id.encode("utf-8")).hexdigest()[:8], 16) % 100
    if bucket < 80:
        return "train"
    if bucket < 90:
        return "validation"
    return "test"


def recommendation_meets_threshold(recommendation: str, minimum: str) -> bool:
    return RECOMMENDATION_ORDER.get(recommendation, 0) >= RECOMMENDATION_ORDER.get(minimum, 0)


def profile_path_for_artist(project_root: Path, artist_id: str) -> Path | None:
    candidates = [
        project_root / "artists" / artist_id / "profile.generated.json",
        project_root / "artists" / artist_id / "profile.json",
    ]
    for path in candidates:
        if path.exists():
            return path
    return None


def sanitized_imagery_tags(track_analysis: dict[str, Any], limit: int = 4) -> list[str]:
    return [entry["tag"] for entry in track_analysis.get("imagery", {}).get("imagery_tags", [])[:limit]]


def dominant_emotions(track_analysis: dict[str, Any], limit: int = 3) -> list[str]:
    counts: dict[str, int] = {}
    for section in track_analysis.get("emotion_arc", {}).get("sections", []):
        emotion = section.get("dominant_emotion")
        if emotion and emotion != "neutral":
            counts[emotion] = counts.get(emotion, 0) + 1
    return [emotion for emotion, _ in sorted(counts.items(), key=lambda item: item[1], reverse=True)[:limit]]


def compatible_modes(profile: dict[str, Any], track_analysis: dict[str, Any], artist_analysis: dict[str, Any]) -> list[dict[str, Any]]:
    artist_mode_scores = {
        item["mode"]: int(item.get("score", 0))
        for item in artist_analysis.get("mode_candidates", [])
        if isinstance(item, dict) and item.get("mode")
    }
    imagery_tags = set(sanitized_imagery_tags(track_analysis, limit=6))
    emotion_tags = set(dominant_emotions(track_analysis, limit=4))

    ranked: list[tuple[int, dict[str, Any]]] = []
    for mode in profile.get("modes", []):
        score = artist_mode_scores.get(mode["mode_id"], 0)
        score += sum(8 for tag in imagery_tags if mode["mode_id"] in MODE_HINT_MAP.get(tag, set()))
        score += sum(2 for focus in mode.get("lyric_focus", []) if focus in imagery_tags or focus in emotion_tags)
        ranked.append((score, mode))

    ranked.sort(key=lambda item: item[0], reverse=True)
    return [mode for score, mode in ranked if score > 0][:2] or profile.get("modes", [])[:2]


def collapse_section_blueprint(mode: dict[str, Any]) -> list[dict[str, Any]]:
    collapsed: list[dict[str, Any]] = []
    seen_sections: set[str] = set()
    for item in mode.get("section_blueprint", []):
        section = item.get("section")
        if not section or section in seen_sections:
            continue
        seen_sections.add(section)
        collapsed.append({"section": section, "goal": item.get("goal", "")})
    return collapsed


def hook_strategy(track_analysis: dict[str, Any]) -> dict[str, Any]:
    repetition = track_analysis.get("repetition", {})
    hook_candidates = repetition.get("hook_candidates", [])
    repeated_lines = repetition.get("repeated_lines", [])
    repeated_openings = repetition.get("repeated_openings", [])
    hook_density = "low"
    if len(hook_candidates) >= 6 or repetition.get("chorus_repetition_score", 0) >= 0.5:
        hook_density = "high"
    elif len(hook_candidates) >= 3 or repeated_lines:
        hook_density = "medium"

    return {
        "hook_density": hook_density,
        "hook_candidate_count": len(hook_candidates),
        "repeated_line_count": len(repeated_lines),
        "repeated_opening_count": len(repeated_openings),
        "chorus_repetition_score": repetition.get("chorus_repetition_score", 0.0),
    }


def infer_song_form(normalized_doc: dict[str, Any], track_analysis: dict[str, Any]) -> dict[str, Any]:
    sections = normalized_doc.get("sections", [])
    if not sections:
        return {
            "confidence": "low",
            "ordered_sections": [],
            "form_labels": [],
            "chorus_anchor_sections": [],
        }

    section_order = [section.get("label", f"section_{index + 1}") for index, section in enumerate(sections)]
    section_index = {label: index for index, label in enumerate(section_order)}
    repetition = track_analysis.get("repetition", {})
    hook_candidates = repetition.get("hook_candidates", [])

    chorus_anchor_sections = {
        section
        for item in repetition.get("repeated_lines", [])
        for section in item.get("sections", [])
        if section in section_index
    }
    chorus_anchor_sections.update(
        item["section"]
        for item in hook_candidates
        if item.get("section") in section_index and (item.get("repeat_count", 0) >= 2 or item.get("score", 0) >= 8.5)
    )

    confidence = "low"
    if chorus_anchor_sections:
        confidence = "high"
    elif hook_candidates:
        top_section = hook_candidates[0].get("section")
        if top_section in section_index:
            chorus_anchor_sections.add(top_section)
            confidence = "medium"

    ordered_chorus_positions = sorted(section_index[section] for section in chorus_anchor_sections)
    inferred_labels: dict[int, tuple[str, str]] = {}

    def assign(position: int, label: str, reason: str) -> None:
        if 0 <= position < len(sections) and position not in inferred_labels:
            inferred_labels[position] = (label, reason)

    if len(sections) == 1:
        assign(0, "single_block", "Only one section was detected in the normalized lyric.")
    elif ordered_chorus_positions:
        first_chorus = ordered_chorus_positions[0]
        last_chorus = ordered_chorus_positions[-1]

        if first_chorus > 0 and int(sections[0].get("line_count", 0)) <= 2 and len(sections) >= 6:
            assign(0, "intro", "Short opening section before the first detected hook cluster.")
            pre_chorus_pool = list(range(1, first_chorus))
        else:
            pre_chorus_pool = list(range(0, first_chorus))

        if pre_chorus_pool:
            if len(pre_chorus_pool) == 1:
                assign(pre_chorus_pool[0], "verse_1", "Single lead-in block before the first chorus.")
            else:
                assign(pre_chorus_pool[0], "verse_1", "Earliest narrative block before the first chorus.")
                for position in pre_chorus_pool[1:-1]:
                    assign(position, "verse_1_extension", "Additional lead-in material before the first chorus.")
                assign(pre_chorus_pool[-1], "pre_chorus", "Last pre-hook block immediately before the first chorus.")

        for chorus_index, position in enumerate(ordered_chorus_positions, start=1):
            if chorus_index == len(ordered_chorus_positions) and len(ordered_chorus_positions) > 1:
                label = "chorus_final"
            elif chorus_index == 1:
                label = "chorus"
            else:
                label = f"chorus_{chorus_index}"
            assign(position, label, "High-hook or repeated material suggests a chorus anchor.")

        interval_counter = 2
        for interval_start, interval_end in zip(ordered_chorus_positions, ordered_chorus_positions[1:]):
            middle_positions = list(range(interval_start + 1, interval_end))
            if not middle_positions:
                continue
            if len(middle_positions) == 1:
                label = "verse_2" if interval_counter == 2 else "bridge"
                reason = "Single transition block between chorus anchors."
                assign(middle_positions[0], label, reason)
            else:
                assign(
                    middle_positions[0],
                    "verse_2" if interval_counter == 2 else "bridge",
                    "First block after a chorus anchor resumes narrative motion.",
                )
                for position in middle_positions[1:-1]:
                    assign(position, "interlude", "Intermediate material between chorus anchors.")
                assign(
                    middle_positions[-1],
                    "pre_chorus_2" if interval_counter == 2 else "bridge_rise",
                    "Final block before the next chorus anchor tightens energy.",
                )
            interval_counter += 1

        trailing_positions = list(range(last_chorus + 1, len(sections)))
        if trailing_positions:
            if len(trailing_positions) == 1:
                trailing_line_count = int(sections[trailing_positions[0]].get("line_count", 0))
                label = "outro" if trailing_line_count <= 2 else "bridge"
                assign(trailing_positions[0], label, "Material after the final chorus anchor.")
            else:
                assign(trailing_positions[0], "bridge", "Post-chorus shift before the ending.")
                for position in trailing_positions[1:-1]:
                    assign(position, "outro_extension", "Extended release after the final chorus.")
                assign(trailing_positions[-1], "outro", "Final release block.")
    else:
        if len(sections) >= 1:
            assign(0, "intro", "No chorus anchor found; using positional fallback for the opening.")
        if len(sections) >= 2:
            assign(1, "verse_1", "Early section fallback.")
        if len(sections) >= 3:
            assign(2, "pre_chorus", "Positional buildup fallback.")
        if len(sections) >= 4:
            assign(3, "chorus", "Best available hook fallback section.")
        if len(sections) >= 5:
            assign(len(sections) - 2, "bridge", "Late-section fallback.")
            assign(len(sections) - 1, "chorus_final", "Final-position fallback.")

    for position, section in enumerate(sections):
        if position not in inferred_labels:
            inferred_labels[position] = ("interlude", "Unassigned section kept as neutral connective material.")

    ordered_sections = [
        {
            "source_section": section_order[position],
            "inferred_label": inferred_labels[position][0],
            "line_count": int(sections[position].get("line_count", 0)),
            "reason": inferred_labels[position][1],
        }
        for position in range(len(sections))
    ]
    return {
        "confidence": confidence,
        "ordered_sections": ordered_sections,
        "form_labels": [item["inferred_label"] for item in ordered_sections],
        "chorus_anchor_sections": [section_order[position] for position in ordered_chorus_positions],
    }


def language_profile(track_analysis: dict[str, Any]) -> dict[str, Any]:
    lexical = track_analysis.get("lexical", {})
    english_ratio = float(lexical.get("english_insertion_ratio", 0.0))
    english_level = "low"
    if english_ratio >= 0.35:
        english_level = "high"
    elif english_ratio >= 0.12:
        english_level = "medium"

    return {
        "dominant_perspective": lexical.get("pronoun_profile", {}).get("dominant_perspective", "undetermined"),
        "english_insertion_level": english_level,
        "line_length_profile": lexical.get("line_length_stats", {}),
        "script_balance": lexical.get("script_balance", {}),
    }


def style_constraints(profile: dict[str, Any], track_analysis: dict[str, Any], artist_analysis: dict[str, Any]) -> dict[str, Any]:
    modes = compatible_modes(profile, track_analysis, artist_analysis)
    style_tags: list[str] = list(profile.get("base_style_tags", []))
    for mode in modes:
        for tag in mode.get("style_tags", []):
            if tag not in style_tags:
                style_tags.append(tag)

    return {
        "style_tags": style_tags[:12],
        "language_policy": profile.get("language_policy", {}),
        "imagery_bank": profile.get("lyric_rules", {}).get("imagery_bank", [])[:10],
        "avoid_terms": profile.get("lyric_rules", {}).get("avoid_terms", []),
        "compatible_modes": [mode["mode_id"] for mode in modes],
    }


def build_track_blueprint_record(
    *,
    artist_id: str,
    normalized_path: Path,
    track_analysis_path: Path,
    artist_analysis_path: Path,
    profile_path: Path,
    normalized_doc: dict[str, Any],
    track_analysis: dict[str, Any],
    artist_analysis: dict[str, Any],
    profile: dict[str, Any],
) -> dict[str, Any]:
    record_id = f"{artist_id}-{normalized_doc['track_id']}-track_blueprint"
    modes = compatible_modes(profile, track_analysis, artist_analysis)
    primary_mode = modes[0] if modes else {}
    inferred_song_form = infer_song_form(normalized_doc, track_analysis)

    return {
        "record_id": record_id,
        "split": deterministic_split(record_id),
        "task_type": "track_blueprint",
        "artist_id": artist_id,
        "artist_name": normalized_doc["artist_name"],
        "track_id": normalized_doc["track_id"],
        "title": normalized_doc["title"],
        "contains_copyrighted_lyrics": False,
        "source_paths": {
            "normalized_document": str(normalized_path),
            "track_analysis": str(track_analysis_path),
            "artist_analysis": str(artist_analysis_path),
            "artist_profile": str(profile_path),
        },
        "instruction": (
            "Build a reusable lyric planning brief from the supplied non-verbatim track evidence. "
            "Preserve artist-consistent imagery, emotional arc, hook density, and section goals without reusing lyrics."
        ),
        "input_context": {
            "artist_summary": profile.get("summary", ""),
            "track_evidence": {
                "observed_section_count": track_analysis.get("structure", {}).get("section_count", 0),
                "has_pre_chorus": track_analysis.get("structure", {}).get("has_pre_chorus", False),
                "has_bridge": track_analysis.get("structure", {}).get("has_bridge", False),
                "has_outro": track_analysis.get("structure", {}).get("has_outro", False),
                "inferred_song_form": inferred_song_form,
                "dominant_imagery_tags": sanitized_imagery_tags(track_analysis),
                "dominant_emotions": dominant_emotions(track_analysis),
                "overall_arc_label": track_analysis.get("emotion_arc", {}).get("overall_arc_label", "undetermined"),
                "hook_strategy": hook_strategy(track_analysis),
                "language_profile": language_profile(track_analysis),
            },
            "artist_frame": {
                "top_imagery_clusters": [
                    item["tag"]
                    for item in artist_analysis.get("imagery_profile", {}).get("top_imagery_clusters", [])[:6]
                ],
                "dominant_arc_patterns": [
                    item["arc"]
                    for item in artist_analysis.get("emotional_profile", {}).get("dominant_arc_patterns", [])[:3]
                ],
                "mode_candidates": [mode["mode_id"] for mode in modes],
            },
        },
        "target": {
            "primary_mode": primary_mode.get("mode_id"),
            "theme_axes": sanitized_imagery_tags(track_analysis) + dominant_emotions(track_analysis),
            "style_constraints": style_constraints(profile, track_analysis, artist_analysis),
            "track_conditioned_structure": inferred_song_form,
            "recommended_structure": collapse_section_blueprint(primary_mode),
            "hook_plan": hook_strategy(track_analysis),
            "generation_notes": [
                "Use only derived artist evidence, not direct lyric reuse.",
                "Keep section contrast aligned with the observed emotional arc.",
                "Favor imagery families that recur across the artist corpus.",
            ],
        },
    }


def build_artist_style_card_record(
    *,
    artist_id: str,
    artist_analysis: dict[str, Any],
    profile: dict[str, Any],
) -> dict[str, Any]:
    record_id = f"{artist_id}-artist_style_card"
    return {
        "record_id": record_id,
        "split": "train",
        "task_type": "artist_style_card",
        "artist_id": artist_id,
        "artist_name": profile.get("display_name", artist_analysis.get("artist_name", artist_id)),
        "contains_copyrighted_lyrics": False,
        "instruction": (
            "Create a compact artist style card for retrieval-time conditioning. "
            "Summarize repeatable imagery, emotional movement, hook behavior, and structural defaults."
        ),
        "input_context": {
            "track_count": artist_analysis.get("track_count", 0),
            "top_imagery_clusters": artist_analysis.get("imagery_profile", {}).get("top_imagery_clusters", [])[:8],
            "dominant_arc_patterns": artist_analysis.get("emotional_profile", {}).get("dominant_arc_patterns", [])[:4],
            "mode_candidates": artist_analysis.get("mode_candidates", [])[:4],
            "common_hook_sections": artist_analysis.get("hook_pattern_summary", {}).get("common_hook_sections", [])[:6],
        },
        "target": {
            "summary": profile.get("summary", ""),
            "style_tags": profile.get("base_style_tags", []),
            "imagery_bank": profile.get("lyric_rules", {}).get("imagery_bank", [])[:10],
            "core_themes": profile.get("lyric_rules", {}).get("themes", [])[:8],
            "structural_defaults": profile.get("lyric_rules", {}).get("structural_defaults", []),
            "mode_cards": [
                {
                    "mode_id": mode.get("mode_id"),
                    "label": mode.get("label"),
                    "lyric_focus": mode.get("lyric_focus", []),
                    "style_tags": mode.get("style_tags", [])[:8],
                }
                for mode in profile.get("modes", [])[:4]
            ],
            "safety_notes": [
                "Use as retrieval and planning context, not as a source of verbatim lyrics.",
                "Keep outputs stylistically adjacent without direct artist naming.",
            ],
        },
    }


def build_training_datasets(
    project_root: Path,
    *,
    audit_payload: dict[str, Any] | None = None,
    minimum_recommendation: str = "needs_review",
    output_dir: Path | None = None,
) -> dict[str, Any]:
    final_output_dir = output_dir or (project_root / "datasets" / "training")
    final_output_dir.mkdir(parents=True, exist_ok=True)

    if audit_payload is None:
        artist_ids = [
            path.stem for path in (project_root / "lyrics" / "analyzed" / "artists").glob("*.json")
        ]
        artists_meta = [{"artist_id": artist_id, "recommendation": "ready", "track_details": []} for artist_id in artist_ids]
    else:
        artists_meta = audit_payload.get("artists", [])

    track_records: list[dict[str, Any]] = []
    artist_records: list[dict[str, Any]] = []
    skipped_artists: list[dict[str, Any]] = []

    for artist_meta in artists_meta:
        artist_id = artist_meta["artist_id"]
        if not recommendation_meets_threshold(artist_meta.get("recommendation", "blocked"), minimum_recommendation):
            skipped_artists.append(
                {
                    "artist_id": artist_id,
                    "reason": f"recommendation_below_threshold:{artist_meta.get('recommendation', 'blocked')}",
                }
            )
            continue

        profile_path = profile_path_for_artist(project_root, artist_id)
        artist_analysis_path = project_root / "lyrics" / "analyzed" / "artists" / f"{artist_id}.json"
        if profile_path is None or not artist_analysis_path.exists():
            skipped_artists.append({"artist_id": artist_id, "reason": "missing_profile_or_artist_analysis"})
            continue

        profile = load_json(profile_path)
        artist_analysis = load_json(artist_analysis_path)
        artist_records.append(
            build_artist_style_card_record(
                artist_id=artist_id,
                artist_analysis=artist_analysis,
                profile=profile,
            )
        )

        track_meta_map = {
            item["track_id"]: item
            for item in artist_meta.get("track_details", [])
            if isinstance(item, dict) and item.get("track_id")
        }
        normalized_root = project_root / "lyrics" / "normalized" / artist_id
        analyzed_root = project_root / "lyrics" / "analyzed" / "tracks" / artist_id
        if not normalized_root.exists() or not analyzed_root.exists():
            skipped_artists.append({"artist_id": artist_id, "reason": "missing_normalized_or_track_analysis_dir"})
            continue

        for normalized_path in sorted(normalized_root.glob("*.json")):
            track_id = normalized_path.stem
            track_meta = track_meta_map.get(track_id)
            if audit_payload is not None:
                if track_meta is None:
                    continue
                if not track_meta.get("training_eligible", False):
                    continue
                if any(issue in BLOCKED_TRACK_ISSUES for issue in track_meta.get("issue_codes", [])):
                    continue

            analysis_path = analyzed_root / f"{track_id}.json"
            if not analysis_path.exists():
                continue

            normalized_doc = load_json(normalized_path)
            track_analysis = load_json(analysis_path)
            track_records.append(
                build_track_blueprint_record(
                    artist_id=artist_id,
                    normalized_path=normalized_path,
                    track_analysis_path=analysis_path,
                    artist_analysis_path=artist_analysis_path,
                    profile_path=profile_path,
                    normalized_doc=normalized_doc,
                    track_analysis=track_analysis,
                    artist_analysis=artist_analysis,
                    profile=profile,
                )
            )

    track_output = write_jsonl(final_output_dir / "track_blueprints.jsonl", track_records)
    artist_output = write_jsonl(final_output_dir / "artist_style_cards.jsonl", artist_records)

    manifest = {
        "schema_version": "1.0",
        "project_root": str(project_root),
        "minimum_recommendation": minimum_recommendation,
        "outputs": {
            "track_blueprints": str(track_output),
            "artist_style_cards": str(artist_output),
        },
        "counts": {
            "track_blueprints": len(track_records),
            "artist_style_cards": len(artist_records),
        },
        "artists_included": sorted({record["artist_id"] for record in track_records + artist_records}),
        "skipped_artists": skipped_artists,
    }
    manifest_output = write_json(final_output_dir / "training_manifest.json", manifest)
    manifest["manifest_path"] = str(manifest_output)
    return manifest
