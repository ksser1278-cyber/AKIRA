from __future__ import annotations

from collections import Counter, defaultdict
from statistics import median
from typing import Any

from .conditioning_brief_dataset import canonical_section
from .lyric_utils import (
    contains_bad_script,
    contains_japanese,
    looks_corrupted_text,
    safe_text,
    unique_preserve_order,
)


def _top(values: list[str], limit: int) -> list[str]:
    counts = Counter(value for value in values if safe_text(value))
    ordered = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return [value for value, _ in ordered[:limit]]


def _clean_atom(value: Any, *, max_len: int = 16) -> str:
    text = safe_text(value)
    if not text:
        return ""
    if not contains_japanese(text):
        return ""
    if contains_bad_script(text) or looks_corrupted_text(text):
        return ""
    compact = text.replace(" ", "")
    if not (2 <= len(compact) <= max_len):
        return ""
    return text


def _clean_phrase(value: Any, *, max_len: int = 96) -> str:
    text = safe_text(value)
    if not text:
        return ""
    if contains_bad_script(text) or looks_corrupted_text(text):
        return ""
    compact = text.replace(" ", "")
    if len(compact) > max_len:
        return ""
    lowered = text.lower()
    if not contains_japanese(text) and lowered.startswith(
        (
            "sets the ",
            "standard ",
            "drives the ",
            "explosive delivery",
            "highest energy state",
            "subverts expectations",
            "introduces ",
            "keeps the ",
            "final release",
        )
    ):
        return ""
    return text


def _default_function(section_name: str) -> str:
    mapping = {
        "intro": "setup",
        "verse_1": "observation",
        "verse_2": "escalation",
        "pre_chorus": "tension_ramp",
        "pre_chorus_2": "tension_ramp_2",
        "chorus": "release",
        "bridge": "exposure",
        "chorus_final": "final_release",
        "outro": "aftertaste",
    }
    return mapping.get(section_name, "narrative")


def _default_title_drop_policy(section_name: str) -> str:
    if section_name == "chorus_final":
        return "primary"
    if section_name == "chorus":
        return "anchor"
    if "pre_chorus" in section_name or section_name == "bridge":
        return "withhold"
    return "sparse"


def _cadence_target(section_name: str, mora_density: str, speed_bias: str) -> str:
    density = safe_text(mora_density).lower()
    speed = safe_text(speed_bias).lower()
    if section_name == "chorus_final":
        return "explosive"
    if density in {"explosive", "burst", "dense"}:
        return "explosive" if speed == "high" else "percussive"
    if density in {"staccato", "tight"}:
        return "tight"
    if density in {"obsessive", "broken"}:
        return "broken"
    if speed == "high":
        return "tight"
    if speed == "low":
        return "open"
    return "medium"


def _abstraction_ceiling(section_name: str, *, imagery_count: int, goal_count: int) -> float:
    defaults = {
        "intro": 0.20,
        "verse_1": 0.18,
        "pre_chorus": 0.15,
        "chorus": 0.12,
        "verse_2": 0.16,
        "pre_chorus_2": 0.13,
        "bridge": 0.20,
        "chorus_final": 0.10,
        "outro": 0.18,
    }
    base = defaults.get(section_name, 0.18)
    if imagery_count >= 3:
        base -= 0.03
    if goal_count == 0:
        base += 0.02
    return round(min(0.28, max(0.08, base)), 2)


def _record_matches_mode(record: dict[str, Any], mode_id: str) -> bool:
    clean_mode_id = safe_text(mode_id).lower()
    if not clean_mode_id:
        return True
    roles = [
        safe_text(value).lower()
        for value in record.get("song_intent", {}).get("narrative_role", [])
        if safe_text(value)
    ]
    if roles and clean_mode_id in roles:
        return True
    primary_mode = safe_text(record.get("primary_mode") or record.get("mode_id")).lower()
    return bool(primary_mode and primary_mode == clean_mode_id)


def _is_synthetic_runtime_record(record: dict[str, Any]) -> bool:
    track_id = safe_text(record.get("track_identity", {}).get("track_id"))
    return bool(track_id and track_id.endswith("_conditioning_vnext"))


def build_section_evidence_bank(records: list[dict[str, Any]], *, mode_id: str = "") -> dict[str, Any]:
    selected_records = [record for record in records if _record_matches_mode(record, mode_id)]
    if not selected_records:
        selected_records = list(records)
    real_records = [record for record in selected_records if not _is_synthetic_runtime_record(record)]
    if real_records:
        selected_records = real_records

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    hook_forces: list[str] = []
    title_styles: list[str] = []
    repetition_counts: list[int] = []
    hook_counts: list[int] = []
    chorus_line_targets: list[int] = []
    global_motifs: list[str] = []
    global_imagery: list[str] = []
    selected_track_ids: list[str] = []

    for record in selected_records:
        identity = record.get("track_identity", {})
        prompt_conditioning = record.get("prompt_conditioning", {})
        song_intent = record.get("song_intent", {})
        lyric_profile = record.get("japanese_lyric_profile", {})
        lyric_ground_truth = record.get("lyric_ground_truth", {})
        analysis_by_name = {
            safe_text(entry.get("section_name")): entry
            for entry in record.get("section_analysis", [])
            if safe_text(entry.get("section_name"))
        }
        track_id = safe_text(identity.get("track_id"))
        if track_id:
            selected_track_ids.append(track_id)

        hook_forces.append(safe_text(lyric_profile.get("hook_copy_force"), "medium"))
        title_styles.append(safe_text(lyric_profile.get("title_ignition_style"), "direct"))
        repetition_counts.append(len(lyric_ground_truth.get("repetition_patterns", [])))
        hook_counts.append(len(lyric_ground_truth.get("hook_lines", [])))

        global_motifs.extend(
            atom
            for atom in (
                _clean_atom(value, max_len=16)
                for value in song_intent.get("key_motifs", [])
            )
            if atom
        )
        global_imagery.extend(
            atom
            for atom in (
                _clean_atom(value, max_len=16)
                for value in prompt_conditioning.get("imagery_anchors", [])
            )
            if atom
        )

        index_map: dict[str, int] = {}
        for section in lyric_ground_truth.get("sections", []):
            canonical = canonical_section(
                safe_text(section.get("section_type")),
                safe_text(section.get("jp_section_role")),
                index_map,
            )
            analysis = analysis_by_name.get(safe_text(section.get("section_name")), {})
            section_vocabulary = [
                atom
                for atom in (
                    _clean_atom(value, max_len=16)
                    for value in analysis.get("vocabulary_focus", [])
                )
                if atom
            ]
            section_imagery = unique_preserve_order(
                section_vocabulary
                + [
                    atom
                    for atom in (
                        _clean_atom(value, max_len=16)
                        for value in prompt_conditioning.get("imagery_anchors", [])
                    )
                    if atom
                ][:2]
            )
            section_motifs = unique_preserve_order(
                [
                    atom
                    for atom in (
                        _clean_atom(value, max_len=16)
                        for value in song_intent.get("key_motifs", [])
                    )
                    if atom
                ]
                + section_vocabulary
                + section_imagery
            )
            narrative_goal = _clean_phrase(analysis.get("narrative_job"), max_len=120)
            cadence = _cadence_target(
                canonical,
                safe_text(section.get("mora_density")),
                safe_text(section.get("spoken_speed_bias")),
            )

            line_count = len(section.get("lines", []))
            if canonical.startswith("chorus") and line_count:
                chorus_line_targets.append(line_count)

            grouped[canonical].append(
                {
                    "track_id": track_id,
                    "line_count": line_count,
                    "narrative_goal": narrative_goal,
                    "required_motifs": section_motifs[:4],
                    "required_imagery": section_imagery[:4],
                    "imagery_focus": section_imagery[:4],
                    "cadence_target": cadence,
                    "phrase_energy_role": _clean_phrase(
                        analysis.get("phrase_energy_role") or section.get("phrase_energy_role"),
                        max_len=40,
                    ),
                    "title_drop_role": _clean_phrase(
                        analysis.get("title_drop_role") or section.get("title_drop_role"),
                        max_len=40,
                    ),
                }
            )

    section_payload: dict[str, dict[str, Any]] = {}
    for section_name, items in grouped.items():
        line_counts = [int(item["line_count"]) for item in items if int(item["line_count"]) > 0]
        narrative_goals = _top([item["narrative_goal"] for item in items], 3)
        required_motifs = unique_preserve_order(
            [
                value
                for item in items
                for value in item.get("required_motifs", [])
                if _clean_atom(value, max_len=16)
            ]
        )[:6]
        imagery_focus = unique_preserve_order(
            [
                value
                for item in items
                for value in item.get("imagery_focus", [])
                if _clean_atom(value, max_len=16)
            ]
        )[:6]
        required_imagery = unique_preserve_order(
            [
                value
                for item in items
                for value in item.get("required_imagery", [])
                if _clean_atom(value, max_len=16)
            ]
        )[:4]
        cadence_votes = _top([item["cadence_target"] for item in items], 1)
        title_drop_roles = _top([item["title_drop_role"] for item in items], 2)
        phrase_energy_roles = _top([item["phrase_energy_role"] for item in items], 2)
        title_drop_policy = _default_title_drop_policy(section_name)
        if any("primary" in role.lower() for role in title_drop_roles):
            title_drop_policy = "primary"
        elif any("anchor" in role.lower() for role in title_drop_roles):
            title_drop_policy = "anchor"
        elif any("withhold" in role.lower() for role in title_drop_roles):
            title_drop_policy = "withhold"

        hook_pressure = "high" if section_name.startswith("chorus") and max(hook_counts or [0]) >= 2 else "medium"

        section_payload[section_name] = {
            "section": section_name,
            "function_hint": _default_function(section_name),
            "narrative_goals": narrative_goals,
            "required_motifs": required_motifs,
            "required_imagery": required_imagery or imagery_focus[:2],
            "imagery_focus": imagery_focus,
            "line_target": int(round(median(line_counts))) if line_counts else 0,
            "cadence_target": cadence_votes[0] if cadence_votes else _cadence_target(section_name, "", ""),
            "abstraction_ceiling": _abstraction_ceiling(
                section_name,
                imagery_count=len(imagery_focus),
                goal_count=len(narrative_goals),
            ),
            "title_drop_policy": title_drop_policy,
            "title_drop_roles": title_drop_roles,
            "phrase_energy_roles": phrase_energy_roles,
            "hook_pressure": hook_pressure,
            "evidence_track_ids": unique_preserve_order(
                [safe_text(item.get("track_id")) for item in items if safe_text(item.get("track_id"))]
            ),
            "source_count": len(items),
        }

    dominant_hook_force = _top(hook_forces, 1)[0] if hook_forces else "medium"
    dominant_title_style = _top(title_styles, 1)[0] if title_styles else "direct"

    return {
        "available": bool(section_payload),
        "mode_id": safe_text(mode_id),
        "record_count": len(selected_records),
        "selected_track_ids": unique_preserve_order(selected_track_ids),
        "global_motifs": unique_preserve_order(global_motifs)[:10],
        "global_imagery": unique_preserve_order(global_imagery)[:10],
        "hook_blueprint": {
            "hook_density": "high" if dominant_hook_force in {"high", "heavy"} else "medium",
            "title_ignition_style": dominant_title_style,
            "chorus_line_target": max(3, int(round(median(chorus_line_targets)))) if chorus_line_targets else 4,
            "hook_line_target": max(2, int(round(median(hook_counts)))) if hook_counts else 2,
            "repetition_pressure": "high" if sum(repetition_counts) >= max(2, len(selected_records)) else "medium",
        },
        "sections": section_payload,
    }
