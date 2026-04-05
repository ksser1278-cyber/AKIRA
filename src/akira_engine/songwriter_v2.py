from __future__ import annotations

import hashlib
import json
import random
import re
from collections import Counter
from pathlib import Path
from typing import Any

from .lyric_draft import (
    arc_label_for_record,
    canonical_section_name,
    choose_record,
    dominant_emotions_for_record,
    extract_section_blocks,
    hook_density_for_record,
    load_jsonl,
    lyric_lines,
    section_goals,
    section_plan,
    style_imagery_bank,
    theme_axes_for_record,
)
from .japanese_lyric_features import build_markdown_japanese_profile
from .alexandria_library import AlexandriaLibrary
from .mastery_blueprint import validate_against_blueprint, get_universal_blueprint
from .phonetic_engine import apply_stutter_glitch, optimize_for_suno_phonetics

_ALEXANDRIA: AlexandriaLibrary | None = None


def _get_alexandria() -> AlexandriaLibrary:
    global _ALEXANDRIA
    if _ALEXANDRIA is None:
        _ALEXANDRIA = AlexandriaLibrary()
    return _ALEXANDRIA

from .direct_emotional_profiles import (
    best_direct_emotional_keyword_match,
    compact_direct_emotional_hook_lines,
    compact_direct_emotional_motifs,
    detect_direct_emotional_profile,
    direct_emotional_motif_seeds,
    direct_emotional_preferred_keywords,
    direct_emotional_profile_section_bank,
    direct_emotional_scene_seeds,
    direct_emotional_track_seed_terms,
    prune_direct_emotional_duplicates,
    direct_emotional_source_variants as build_direct_emotional_source_variants,
)
from .dark_cute_profiles import build_dark_cute_section_bank, default_cute_word
from .intimate_profiles import detect_intimate_profile, intimate_profile_section_bank
from .night_drive_profiles import night_drive_profile_section_bank
from .anthemic_profiles import detect_anthemic_profile, anthemic_profile_section_bank
from .mode_support_runtime import load_mode_support_context
from .reporting import write_utf8_json, write_utf8_text
from .lyric_utils import (
    unique_preserve_order,
    is_safe_prompt_term,
    is_safe_lyric_term,
    looks_corrupted_text,
    extract_japanese_lexical_atoms,
)
from .songwriter_io import (
    project_root,
    load_artist_profile,
    load_structure_profile,
    load_representative_demo_profile,
    normalize_lookup_text,
    load_conditioning_records,
    load_generated_mode_assignments,
    matching_conditioning_record,
    resolve_primary_mode,
    resolve_default_track_id,
)

GENERIC_HOOK_ATOMS = {"心", "声", "夜", "夢", "光", "君", "僕", "私", "明日", "未来", "名前"}




def resolved_theme_axes_for_record(record: dict[str, Any]) -> list[str]:
    override = record.get("_override_theme_axes")
    if override:
        return list(override)
    return theme_axes_for_record(record)


def resolved_dominant_emotions_for_record(record: dict[str, Any]) -> list[str]:
    override = record.get("_override_dominant_emotions")
    if override:
        return list(override)
    return dominant_emotions_for_record(record)




DIRECT_EMOTIONAL_HARD_CASE_TRACKS = {
    "deco27_yumeyume",
}




def unique_phrase_list(values: list[Any]) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()
    for value in values:
        cleaned = " ".join(str(value or "").strip().split())
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            output.append(cleaned)
    return output


def clone_conditioning_hint(hint: dict[str, Any]) -> dict[str, Any]:
    cloned: dict[str, Any] = {}
    for key, value in hint.items():
        cloned[key] = value[:] if isinstance(value, list) else value
    return cloned


def abstract_conditioning_support_lines(atoms: list[str], *, limit: int = 2) -> list[str]:
    safe_atoms = [item for item in atoms if is_safe_lyric_term(item)]
    if not safe_atoms:
        return []
    if len(safe_atoms) == 1:
        return [safe_atoms[0]]

    support_lines: list[str] = []
    for index in range(len(safe_atoms) - 1):
        left = safe_atoms[index]
        right = safe_atoms[index + 1]
        if left == right:
            continue
        support_lines.append(f"{left} {right}")
        if len(support_lines) >= limit:
            break
    if not support_lines:
        support_lines.append(safe_atoms[0])
    return support_lines[:limit]


def retarget_conditioning_hint(target: str, hint: dict[str, Any], conditioning: dict[str, Any]) -> dict[str, Any]:
    adapted = clone_conditioning_hint(hint)
    source_role = str(adapted.get("jp_role") or "")
    source_atoms = [
        item
        for item in adapted.get("conditioning_atoms", [])
        if is_safe_lyric_term(item) and item not in LOW_SIGNAL_CONDITIONING_ATOMS
    ]
    chorus_atoms = conditioning_hook_atoms(conditioning)
    contrast_atoms = conditioning_contrast_terms(conditioning)
    support_atoms = high_signal_conditioning_atoms(
        list(conditioning.get("song_intent", {}).get("key_motifs", []))
        + list(conditioning.get("prompt_conditioning", {}).get("imagery_anchors", [])),
        limit=8,
        allow_generic=True,
    )

    if target in {"pre_chorus", "pre_chorus_2"} and source_role != "b_melo":
        section_atoms = unique_preserve_order(
            contrast_atoms[:2] + chorus_atoms[:1] + support_atoms[:2] + source_atoms[:2]
        )
        adapted["required_motifs"] = section_atoms[:4]
        adapted["conditioning_atoms"] = unique_preserve_order(section_atoms + source_atoms)[:6]
        adapted["delivery"] = "lift"
        if not adapted.get("scene") or str(adapted.get("scene")) in LOW_SIGNAL_CONDITIONING_ATOMS:
            adapted["scene"] = contrast_atoms[0] if contrast_atoms else adapted.get("scene")

    if target == "outro" and source_role != "outro":
        tail_atoms = [
            item
            for item in source_atoms
            if item not in {"故にどんな", "笑おう"}
        ]
        preferred_tail = [item for item in tail_atoms if re.search(r"[ァ-ヶー]", item)]
        if not preferred_tail:
            preferred_tail = tail_atoms[-2:] if len(tail_atoms) >= 2 else tail_atoms
        section_atoms = unique_preserve_order(
            chorus_atoms[:1] + preferred_tail[:2] + support_atoms[:2] + contrast_atoms[1:2]
        )
        adapted["required_motifs"] = section_atoms[:4]
        adapted["conditioning_atoms"] = unique_preserve_order(section_atoms + source_atoms)[:6]
        adapted["delivery"] = "suspended"

    return adapted


def target_section_for_jp_role(role: str, index: int) -> str | None:
    if role == "intro":
        return "intro"
    if role == "a_melo":
        return "verse_1" if index == 0 else "verse_2"
    if role == "b_melo":
        return "pre_chorus" if index == 0 else "pre_chorus_2"
    if role == "sabi":
        return "chorus" if index == 0 else "chorus_2"
    if role == "dai_sabi":
        return "chorus_final"
    if role == "c_melo":
        return "bridge" if index == 0 else "bridge_rise"
    if role == "outro":
        return "outro"
    return None


def build_conditioning_section_hints(conditioning: dict[str, Any]) -> dict[str, dict[str, Any]]:
    song_intent = conditioning.get("song_intent", {})
    lyric_sections = conditioning.get("lyric_ground_truth", {}).get("sections", [])
    section_analysis = conditioning.get("section_analysis", [])
    jp_profile = conditioning.get("japanese_lyric_profile", {})
    prompt_conditioning = conditioning.get("prompt_conditioning", {})
    chorus_atoms = [item for item in conditioning_hook_atoms(conditioning) if item not in GENERIC_HOOK_ATOMS]

    analysis_lookup = {
        (entry.get("section_name"), entry.get("section_type")): entry
        for entry in section_analysis
    }
    jp_lookup = {
        (entry.get("section_name"), entry.get("section_type")): entry
        for entry in jp_profile.get("section_features", [])
    }

    role_counts: Counter[str] = Counter()
    hints: dict[str, dict[str, Any]] = {}
    pending_sabi_targets: list[tuple[str, dict[str, Any]]] = []
    role_hints: dict[str, list[dict[str, Any]]] = {}

    for section in lyric_sections:
        name = section.get("section_name")
        section_type = section.get("section_type")
        analysis = analysis_lookup.get((name, section_type), {})
        jp_entry = jp_lookup.get((name, section_type), {})
        role = (
            section.get("jp_section_role")
            or analysis.get("jp_section_role")
            or jp_entry.get("jp_section_role")
            or "other"
        )
        target = target_section_for_jp_role(role, role_counts[role])
        role_counts[role] += 1
        if not target:
            continue

        vocab = normalize_conditioning_terms(
            list(analysis.get("vocabulary_focus", []))
            + list(song_intent.get("key_motifs", []))
            + list(prompt_conditioning.get("imagery_anchors", []))
        )
        section_atoms = high_signal_conditioning_atoms(section.get("lines", []), limit=6, allow_generic=True)
        goal_parts = []
        if analysis.get("narrative_job"):
            goal_parts.append(str(analysis["narrative_job"]))
        goal_parts.extend(str(item) for item in analysis.get("lyric_function", [])[:2])
        phrase_energy_role = (
            section.get("phrase_energy_role")
            or analysis.get("phrase_energy_role")
            or jp_entry.get("phrase_energy_role")
            or ""
        )
        if phrase_energy_role == "compression":
            goal_parts.append("Tighten the language before the hook opens.")
        elif phrase_energy_role == "release":
            goal_parts.append("Let the hook land clearly and memorably.")
        elif phrase_energy_role == "pivot":
            goal_parts.append("Shift the emotional angle before the final release.")

        delivery = {
            "observation": "narrative",
            "compression": "lift",
            "release": "hook-first",
            "pivot": "suspended",
            "afterglow": "suspended",
        }.get(str(phrase_energy_role), None)

        lyric_vocab = unique_preserve_order(
            section_atoms
            + [item for item in vocab if is_safe_lyric_term(item)]
        )
        if role in {"sabi", "dai_sabi"}:
            lyric_vocab = unique_preserve_order(chorus_atoms + lyric_vocab)
        hint = {
            "goal": " ".join(unique_phrase_list(goal_parts)) or None,
            "scene": next((item for item in section_atoms if is_safe_lyric_term(item)), None)
            or next((item for item in lyric_vocab if is_safe_lyric_term(item)), None),
            "required_motifs": lyric_vocab[:4],
            "conditioning_atoms": lyric_vocab[:6],
            # Keep semantic residue from references, not reusable surface lines.
            "source_lines": abstract_conditioning_support_lines(section_atoms[:4]),
            "source_atoms": section_atoms[:6],
            "question_heads": question_heads_from_lines(section.get("lines", [])),
            "has_questions": section_has_question(section.get("lines", [])),
            "delivery": delivery,
            "jp_role": role,
        }
        role_hints.setdefault(role, []).append(clone_conditioning_hint(hint))
        if role == "sabi":
            pending_sabi_targets.append((target, hint))
        if target not in hints:
            hints[target] = hint

    def first_role_hint(*roles: str) -> dict[str, Any] | None:
        for role_name in roles:
            candidates = role_hints.get(role_name, [])
            if candidates:
                return clone_conditioning_hint(candidates[0])
        return None

    def last_role_hint(*roles: str) -> dict[str, Any] | None:
        for role_name in roles:
            candidates = role_hints.get(role_name, [])
            if candidates:
                return clone_conditioning_hint(candidates[-1])
        return None

    if "verse_1" not in hints:
        verse_hint = first_role_hint("a_melo")
        if verse_hint:
            hints["verse_1"] = retarget_conditioning_hint("verse_1", verse_hint, conditioning)
    if "verse_2" not in hints:
        verse_hint = last_role_hint("a_melo")
        if verse_hint:
            hints["verse_2"] = retarget_conditioning_hint("verse_2", verse_hint, conditioning)
    if "pre_chorus" not in hints:
        pre_hint = first_role_hint("b_melo", "sabi", "a_melo")
        if pre_hint:
            hints["pre_chorus"] = retarget_conditioning_hint("pre_chorus", pre_hint, conditioning)
    if "pre_chorus_2" not in hints:
        pre_hint = last_role_hint("b_melo", "dai_sabi", "sabi", "a_melo")
        if pre_hint:
            hints["pre_chorus_2"] = retarget_conditioning_hint("pre_chorus_2", pre_hint, conditioning)
    if "chorus" not in hints:
        chorus_hint = first_role_hint("sabi", "dai_sabi")
        if chorus_hint:
            hints["chorus"] = retarget_conditioning_hint("chorus", chorus_hint, conditioning)
    if "chorus_final" not in hints and pending_sabi_targets:
        hints["chorus_final"] = retarget_conditioning_hint("chorus_final", pending_sabi_targets[-1][1], conditioning)
    if "chorus_final" not in hints:
        chorus_hint = last_role_hint("dai_sabi", "sabi", "a_melo")
        if chorus_hint:
            hints["chorus_final"] = retarget_conditioning_hint("chorus_final", chorus_hint, conditioning)
    if "bridge" not in hints:
        bridge_hint = first_role_hint("c_melo", "dai_sabi", "sabi", "a_melo")
        if bridge_hint:
            hints["bridge"] = retarget_conditioning_hint("bridge", bridge_hint, conditioning)
    if "bridge_rise" not in hints:
        bridge_hint = last_role_hint("c_melo", "dai_sabi", "sabi", "a_melo")
        if bridge_hint:
            hints["bridge_rise"] = retarget_conditioning_hint("bridge_rise", bridge_hint, conditioning)
    if "outro" not in hints:
        outro_hint = last_role_hint("outro", "c_melo", "a_melo", "dai_sabi", "sabi")
        if outro_hint:
            hints["outro"] = retarget_conditioning_hint("outro", outro_hint, conditioning)
    return hints


def conditioning_motif_roster(conditioning: dict[str, Any], theme_axes: list[str], rng: random.Random) -> list[dict[str, Any]] | None:
    song_intent = conditioning.get("song_intent", {})
    prompt_conditioning = conditioning.get("prompt_conditioning", {})
    section_analysis = conditioning.get("section_analysis", [])
    hook_atoms = conditioning_hook_atoms(conditioning)
    title_atoms = conditioning_title_atoms(conditioning)
    contrast_atoms = conditioning_contrast_terms(conditioning)
    recurring_atoms = recurring_conditioning_lyric_atoms(conditioning, min_count=2, limit=8)
    lyric_atoms = dense_conditioning_lyric_atoms(conditioning, limit=14)

    structured_motif_values = normalize_conditioning_terms(
        list(song_intent.get("key_motifs", []))
        + list(prompt_conditioning.get("imagery_anchors", []))
        + [word for entry in section_analysis for word in entry.get("vocabulary_focus", [])]
    )
    motif_pool = unique_phrase_list(
        title_atoms
        + hook_atoms
        + lyric_atoms
        + contrast_atoms
        + recurring_atoms
        + high_signal_conditioning_atoms(structured_motif_values, limit=12, allow_generic=True)
    )[:14]
    structured_scene_values = normalize_conditioning_terms(
        list(prompt_conditioning.get("imagery_anchors", []))
        + [entry.get("narrative_job", "") for entry in section_analysis]
        + list(song_intent.get("contrast_device", []))
    )
    scene_pool = unique_phrase_list(
        lyric_atoms
        + recurring_atoms
        + contrast_atoms
        + high_signal_conditioning_atoms(structured_scene_values, limit=10, allow_generic=True)
    )[:12]
    safe_motifs = [item for item in motif_pool if is_safe_lyric_term(item)]
    safe_scenes = [item for item in scene_pool if is_safe_lyric_term(item)]
    if not safe_motifs:
        return None

    roster: list[dict[str, Any]] = []
    cursor = 0
    axes = theme_axes or ["conditioning"]
    for axis in axes:
        motifs = safe_motifs[cursor: cursor + 3] or safe_motifs[:3]
        scenes = safe_scenes[cursor: cursor + 3] or safe_scenes[:3] or motifs[:2]
        roster.append(
            {
                "axis": axis,
                "motifs": unique_preserve_order(motifs)[:3],
                "scene_candidates": unique_preserve_order(scenes)[:3],
            }
        )
        cursor += 2
    return roster


def conditioning_hook_core(conditioning: dict[str, Any], fallback: str) -> str:
    song_intent = conditioning.get("song_intent", {})
    prompt_conditioning = conditioning.get("prompt_conditioning", {})
    candidates = unique_phrase_list(
        conditioning_contrast_terms(conditioning)
        + normalize_conditioning_terms(
            list(song_intent.get("key_motifs", []))
            + list(prompt_conditioning.get("imagery_anchors", []))
        )
        + recurring_conditioning_lyric_atoms(conditioning, min_count=2, limit=6)
        + conditioning_hook_atoms(conditioning)
        + conditioning_title_atoms(conditioning)
        + conditioning_hook_phrases(conditioning)
    )
    safe_candidates = [item for item in candidates if is_safe_lyric_term(item)]
    preferred = [item for item in safe_candidates if item not in GENERIC_HOOK_ATOMS]
    if preferred:
        return preferred[0]
    return safe_candidates[0] if safe_candidates else fallback


def conditioning_semantic_hook_atoms(conditioning: dict[str, Any]) -> list[str]:
    song_intent = conditioning.get("song_intent", {})
    prompt_conditioning = conditioning.get("prompt_conditioning", {})
    section_analysis = conditioning.get("section_analysis", [])
    values = normalize_conditioning_terms(
        list(song_intent.get("key_motifs", []))
        + list(song_intent.get("contrast_device", []))
        + list(prompt_conditioning.get("imagery_anchors", []))
        + [word for entry in section_analysis for word in entry.get("vocabulary_focus", [])]
    )
    atoms = high_signal_conditioning_atoms(values, limit=10, allow_generic=True)
    return [item for item in atoms if item not in conditioning_hook_phrases(conditioning)]


def conditioning_hook_text(
    conditioning: dict[str, Any],
    *,
    mode_bank: dict[str, list[str]],
    fallback_core: str,
    rng: random.Random,
) -> tuple[str, str]:
    hook_shape = detect_conditioning_hook_style(conditioning)
    hook_phrases = [
        phrase
        for phrase in conditioning_hook_phrases(conditioning)
        if is_safe_lyric_term(phrase) and phrase.lower() not in {"let", "go"}
    ]
    hook_core = conditioning_hook_core(conditioning, fallback_core)
    if hook_phrases:
        preferred = [phrase for phrase in hook_phrases if phrase not in GENERIC_HOOK_ATOMS]
        direct = preferred[0] if preferred else hook_phrases[0]
        if hook_shape.get("chant_mode") or len(direct) <= 10 or hook_shape.get("appeal_mode"):
            return direct, direct
        return f"{rng.choice(mode_bank['hook_prefixes'])}{direct}", direct
    return f"{rng.choice(mode_bank['hook_prefixes'])}{hook_core}は{rng.choice(mode_bank['hook_verbs'])}", hook_core


def normalize_conditioning_term(value: Any) -> str:
    text = " ".join(str(value or "").strip().split())
    if not text:
        return ""
    lowered = text.lower()
    if lowered in CONDITIONING_TERM_NORMALIZATION:
        return CONDITIONING_TERM_NORMALIZATION[lowered]

    normalized = text
    for source, target in sorted(CONDITIONING_TERM_NORMALIZATION.items(), key=lambda item: len(item[0]), reverse=True):
        normalized = re.sub(re.escape(source), target, normalized, flags=re.IGNORECASE)

    normalized = re.sub(r"\([^)]*\)", "", normalized)
    normalized = re.sub(r"\bvs\b", "と", normalized, flags=re.IGNORECASE)
    normalized = normalized.replace("/", " ").replace("-", " ")
    normalized = re.sub(r"[,:;]", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def normalize_conditioning_terms(values: list[Any]) -> list[str]:
    normalized: list[str] = []
    for value in values:
        phrase = normalize_conditioning_term(value)
        if not phrase:
            continue
        chunks = [chunk.strip() for chunk in re.split(r"\s+と\s+|\s+", phrase) if chunk.strip()]
        if is_safe_lyric_term(phrase):
            normalized.append(phrase)
        normalized.extend(chunk for chunk in chunks if is_safe_lyric_term(chunk))
    return unique_phrase_list(normalized)

LOW_SIGNAL_CONDITIONING_ATOMS = {
    "意味", "容易く", "正確", "感情", "判断", "分別", "証明", "不明瞭", "証明しよう",
    "どうし", "見抜いて", "吐いて", "打つんだ", "聞き", "逸ら", "分けてみせ", "論理",
    "不合理な", "禁じ",
}
CONDITIONED_DECISION_BANK = [
    "それでも黙らない",
    "壊れたまま飲み込まない",
    "ここから誤魔化さない",
    "ここから飲み込まない",
    "喉の奥で噛み砕く",
    "このまま引き受ける",
]
CONDITIONED_RELEASE_BANK = [
    "綺麗に切れなくても",
    "答えにならなくても",
    "誤差のままでも",
    "うまく名前がなくても",
]




def conditioning_lyric_lines(conditioning: dict[str, Any]) -> list[str]:
    lyric_ground_truth = conditioning.get("lyric_ground_truth", {})
    lines: list[str] = []
    for section in lyric_ground_truth.get("sections", []):
        lines.extend(str(line).strip() for line in section.get("lines", []) if str(line or "").strip())
    return lines


def conditioning_title_atoms(conditioning: dict[str, Any]) -> list[str]:
    title = conditioning.get("track_identity", {}).get("title", "")
    candidates: list[str] = []
    if is_safe_lyric_term(title):
        candidates.append(str(title).strip())
    candidates.extend(extract_japanese_lexical_atoms([title], limit=4))
    return unique_preserve_order(candidates)[:4]


def conditioning_hook_lines(conditioning: dict[str, Any]) -> list[str]:
    lyric_ground_truth = conditioning.get("lyric_ground_truth", {})
    return [str(line).strip() for line in lyric_ground_truth.get("hook_lines", []) if str(line or "").strip()]


def compact_conditioning_hook_phrase(value: Any) -> str:
    text = normalize_conditioning_term(value)
    if not text:
        return ""
    if " " in text:
        first_token = text.split()[0].strip()
        if first_token:
            text = first_token
    text = re.sub(r"[\uac00-\ud7af]+", "", text).strip()
    compact = re.sub(r"^[0-9０-９\.\,、\s]+で?", "", text).strip()
    return compact if compact else text


def conditioning_hook_phrases(conditioning: dict[str, Any]) -> list[str]:
    phrases: list[str] = []
    raw_values = conditioning_hook_lines(conditioning) + [conditioning.get("track_identity", {}).get("title", "")]
    for value in raw_values:
        text = str(value or "").strip()
        if not text:
            continue
        compact = compact_conditioning_hook_phrase(text)
        has_count_in = bool(re.match(r"^[0-9０-９\.\,、\s]+で", normalize_conditioning_term(text)))
        if not has_count_in and is_safe_lyric_term(text) and len(text) <= 16:
            phrases.append(text)
        if compact != text and is_safe_lyric_term(compact) and len(compact) <= 16:
            phrases.append(compact)
        tokens = [
            token.strip("「」『』()[] ")
            for token in re.split(r"[\s/／,，、。!！?？・]+", text)
            if token.strip("「」『』()[] ")
        ]
        for token in tokens:
            if re.search(r"[\uac00-\ud7af]", token):
                continue
            if is_safe_lyric_term(token) and len(token) <= 16:
                phrases.append(token)
    return unique_preserve_order(phrases)


def short_conditioning_phrases_from_lines(
    lines: list[str],
    *,
    limit: int | None = None,
) -> list[str]:
    phrases: list[str] = []
    seen: set[str] = set()
    for line in lines:
        normalized = normalize_conditioning_term(line)
        if not normalized:
            continue
        fragments = [normalized]
        fragments.extend(
            fragment.strip("「」『』()[] ")
            for fragment in re.split(r"[ 　]+|(?<=[ぁ-んァ-ン一-龯])(?:が|を|に|へ|と|で|は|も)(?=[ぁ-んァ-ン一-龯])", normalized)
            if fragment.strip("「」『』()[] ")
        )
        for fragment in fragments:
            if len(fragment) < 2 or len(fragment) > 18:
                continue
            if not is_safe_lyric_term(fragment):
                continue
            if fragment in LOW_SIGNAL_CONDITIONING_ATOMS or fragment in GENERIC_HOOK_ATOMS:
                continue
            if fragment not in seen:
                seen.add(fragment)
                phrases.append(fragment)
                if limit is not None and len(phrases) >= limit:
                    return phrases
    return phrases


def conditioning_short_lyric_phrases(
    conditioning: dict[str, Any],
    *,
    limit: int | None = None,
) -> list[str]:
    return short_conditioning_phrases_from_lines(conditioning_lyric_lines(conditioning), limit=limit)


def high_signal_conditioning_atoms(
    values: list[Any],
    *,
    limit: int | None = None,
    allow_generic: bool = False,
) -> list[str]:
    atoms = extract_japanese_lexical_atoms(normalize_conditioning_terms(values))
    filtered: list[str] = []
    for atom in atoms:
        if not is_safe_lyric_term(atom):
            continue
        if atom in LOW_SIGNAL_CONDITIONING_ATOMS:
            continue
        if any(marker in atom for marker in LOW_SIGNAL_CONDITIONING_ATOMS):
            continue
        if not allow_generic and atom in GENERIC_HOOK_ATOMS:
            continue
        filtered.append(atom)
        if limit is not None and len(filtered) >= limit:
            break
    return unique_preserve_order(filtered)


def conditioning_hook_atoms(conditioning: dict[str, Any]) -> list[str]:
    hook_lines = conditioning_hook_lines(conditioning)
    compact_hook_lines = [compact_conditioning_hook_phrase(line) for line in hook_lines]
    compact_hook_lines = [line for line in compact_hook_lines if line]
    hook_phrases = conditioning_hook_phrases(conditioning)
    title = str(conditioning.get("track_identity", {}).get("title", "")).strip()
    compound_phrases = [
        phrase
        for phrase in hook_phrases
        if is_safe_lyric_term(phrase) and 4 <= len(phrase) <= 16
    ]
    atoms = high_signal_conditioning_atoms(
        compound_phrases + compact_hook_lines + [title],
        limit=8,
    )
    if atoms:
        filtered_atoms = [
            atom
            for atom in atoms
            if not (
                len(atom) <= 3
                and atom not in title
                and any(atom != phrase and atom in phrase for phrase in compound_phrases)
            )
        ]
        return unique_preserve_order(compound_phrases + filtered_atoms)[:8]
    fallback = hook_phrases + extract_japanese_lexical_atoms(
        compact_hook_lines + [title],
        limit=8,
    )
    return unique_preserve_order(fallback)[:8]


def recurring_conditioning_lyric_atoms(
    conditioning: dict[str, Any],
    *,
    min_count: int = 2,
    limit: int | None = None,
) -> list[str]:
    counts: Counter[str] = Counter()
    for line in conditioning_lyric_lines(conditioning):
        for atom in extract_japanese_lexical_atoms([line]):
            if not is_safe_lyric_term(atom):
                continue
            if atom in LOW_SIGNAL_CONDITIONING_ATOMS or atom in GENERIC_HOOK_ATOMS:
                continue
            counts[atom] += 1
    ordered = [atom for atom, count in counts.most_common() if count >= min_count]
    if limit is not None:
        ordered = ordered[:limit]
    return ordered


def dense_conditioning_lyric_atoms(
    conditioning: dict[str, Any],
    *,
    limit: int | None = None,
) -> list[str]:
    low_signal_exact = {
        "世界",
        "今日",
        "本当",
        "何処",
        "果てず",
        "湧く",
        "今日も",
        "今に",
    }
    low_signal_suffixes = (
        "なんて",
        "だけ",
        "ほど",
        "まで",
        "でも",
        "より",
        "して",
        "した",
        "する",
        "ない",
        "たい",
        "てる",
        "れる",
        "られる",
        "よう",
        "みたい",
        "まま",
        "こそ",
        "さえ",
        "ぐらい",
        "くらい",
        "ながら",
        "とか",
        "など",
        "から",
        "ので",
    )

    def signal_score(atom: str) -> int:
        cleaned = str(atom or "").strip()
        kanji = len(re.findall(r"[\u4e00-\u9fff々]", cleaned))
        katakana = len(re.findall(r"[\u30a1-\u30fa\u30fc]", cleaned))
        hiragana = len(re.findall(r"[\u3041-\u3096]", cleaned))
        score = kanji * 4 + katakana * 3 + max(0, len(cleaned) - hiragana)
        if cleaned in low_signal_exact:
            score -= 6
        if any(cleaned.endswith(suffix) for suffix in low_signal_suffixes):
            score -= 8
        if hiragana >= max(2, len(cleaned) // 2):
            score -= 6
        if kanji + katakana >= 2 and len(cleaned) <= 5:
            score += 4
        return score

    counts: Counter[str] = Counter()
    first_seen: dict[str, int] = {}
    cursor = 0
    for line in conditioning_lyric_lines(conditioning):
        for atom in extract_japanese_lexical_atoms([line], limit=12):
            if not is_safe_lyric_term(atom):
                continue
            if atom in LOW_SIGNAL_CONDITIONING_ATOMS or atom in GENERIC_HOOK_ATOMS:
                continue
            counts[atom] += 1
            if atom not in first_seen:
                first_seen[atom] = cursor
                cursor += 1
    ordered = [
        atom
        for atom, _count in sorted(
            counts.items(),
            key=lambda item: (-item[1], -signal_score(item[0]), first_seen.get(item[0], 10**6), -len(item[0])),
        )
    ]
    if limit is not None:
        ordered = ordered[:limit]
    return ordered


def conditioning_contrast_terms(conditioning: dict[str, Any]) -> list[str]:
    song_intent = conditioning.get("song_intent", {})
    normalized = normalize_conditioning_terms(list(song_intent.get("contrast_device", [])))
    atoms = high_signal_conditioning_atoms(normalized, limit=8, allow_generic=True)
    if atoms:
        return atoms
    return extract_japanese_lexical_atoms(normalized, limit=8)


def section_has_question(lines: list[str]) -> bool:
    return any(("?" in line) or ("？" in line) for line in lines)


def question_heads_from_lines(lines: list[str]) -> list[str]:
    heads: list[str] = []
    for line in lines:
        cleaned = str(line or "").strip()
        if not cleaned:
            continue
        if "?" not in cleaned and "？" not in cleaned:
            continue
        match = re.match(r"(.{2,14}?)はどう", cleaned)
        if not match:
            match = re.match(r"(.{2,14}?)は", cleaned)
        if not match:
            continue
        head = match.group(1).strip("「」『』 ")
        if len(head) >= 2:
            heads.append(head)
    return unique_phrase_list(heads)


def detect_conditioning_hook_style(conditioning: dict[str, Any]) -> dict[str, Any]:
    hook_lines = conditioning_hook_lines(conditioning)
    chorus_lines: list[str] = []
    for section in conditioning.get("lyric_ground_truth", {}).get("sections", []):
        role = section.get("jp_section_role")
        if role in {"sabi", "dai_sabi"}:
            chorus_lines.extend(str(line).strip() for line in section.get("lines", []) if str(line or "").strip())
    question_driven = section_has_question(hook_lines) or section_has_question(chorus_lines)
    appeal_mode = any(str(line).strip().endswith(("てよ", "でよ", "ないで", "くれ")) for line in hook_lines)
    chant_mode = len(hook_lines) == 1 and len(str(hook_lines[0])) <= 8
    return {
        "question_driven": question_driven,
        "appeal_mode": appeal_mode,
        "chant_mode": chant_mode,
        "question_heads": question_heads_from_lines(chorus_lines),
    }


def conditioning_theme_axes(conditioning: dict[str, Any], fallback_axes: list[str]) -> list[str]:
    song_intent = conditioning.get("song_intent", {})
    prompt_conditioning = conditioning.get("prompt_conditioning", {})
    values = [
        *song_intent.get("core_theme", []),
        song_intent.get("emotional_thesis", ""),
        *song_intent.get("contrast_device", []),
        *song_intent.get("dramatic_arc", []),
        *song_intent.get("key_motifs", []),
        *prompt_conditioning.get("imagery_anchors", []),
    ]
    text = " ".join(str(value or "").lower() for value in values)
    hits: list[tuple[int, str]] = []
    for axis, keywords in CONDITIONING_AXIS_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in text)
        if score:
            hits.append((score, axis))
    if not hits:
        return fallback_axes
    ordered = [axis for _, axis in sorted(hits, key=lambda item: (-item[0], item[1]))]
    return unique_preserve_order(ordered + fallback_axes)[:3]


def conditioning_dominant_emotions(conditioning: dict[str, Any], fallback: list[str]) -> list[str]:
    song_intent = conditioning.get("song_intent", {})
    values = [
        *song_intent.get("core_theme", []),
        song_intent.get("emotional_thesis", ""),
        *song_intent.get("contrast_device", []),
        *song_intent.get("dramatic_arc", []),
    ]
    text = " ".join(str(value or "").lower() for value in values)
    hits: list[tuple[int, str]] = []
    for emotion, keywords in CONDITIONING_EMOTION_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in text)
        if score:
            hits.append((score, emotion))
    if not hits:
        return fallback
    ordered = [emotion for _, emotion in sorted(hits, key=lambda item: (-item[0], item[1]))]
    return unique_preserve_order(ordered + fallback)[:3]


def support_enabled_for_record(record: dict[str, Any], conditioning: dict[str, Any] | None) -> bool:
    artist_id = str(record.get("artist_id", "")).strip().lower()
    if not conditioning:
        return True
    return artist_id not in {"pinocchiop", "deco27"}


def merge_mode_support_roster(
    roster: list[dict[str, Any]],
    support_context: dict[str, Any],
) -> list[dict[str, Any]]:
    if not support_context.get("available") or not roster:
        return roster

    motif_atoms = [item for item in support_context.get("motif_atoms", []) if is_safe_lyric_term(item)]
    scene_atoms = [item for item in support_context.get("scene_atoms", []) if is_safe_lyric_term(item)]
    if not motif_atoms and not scene_atoms:
        return roster

    merged: list[dict[str, Any]] = []
    for index, item in enumerate(roster):
        motifs = list(item.get("motifs", []))
        scenes = list(item.get("scene_candidates", []))
        if index < 2:
            motifs = unique_preserve_order(motifs + motif_atoms[:2])[:4]
            scenes = unique_preserve_order(scenes + scene_atoms[:2])[:4]
        merged.append(
            {
                **item,
                "motifs": motifs,
                "scene_candidates": scenes or motifs[:3],
            }
        )
    return merged


THEME_SCENES = {
    "body": ["胸の内側", "喉の奥", "まぶたの裏", "手のひらの温度"],
    "noise": ["駅前のざわめき", "遠くで軋むスピーカー", "夜に残る残響"],
    "time": ["秒針の鳴る部屋", "夜明けの手前", "昨日の続き", "朝の輪郭"],
    "defiance": ["逆風の交差点", "引き返せない坂道", "歯を食いしばる高架下"],
    "light": ["逆光のホーム", "白線のきわ", "残照の窓辺", "光の粒が揺れる路地"],
    "city": ["ネオンの路地", "高架下の湿った影", "信号待ちの横断歩道"],
    "fracture": ["ひび割れたガラス越し", "継ぎ目だらけの夜道", "欠片の散る足元"],
    "vulnerability": ["誰もいない踊り場", "眠れないままの部屋", "触れたらほどけそうな距離"],
    "motion": ["駆け出す寸前のホーム", "足音だけが先に行く道", "走り出した風の中"],
    "uplift": ["追い風の吹く非常階段", "浮力だけが残る夜空", "明るくなりきらない空"],
    "weather": ["雨上がりの歩道橋", "風向きの変わる角", "霧のかかった信号"],
    "night": ["真夜中の交差点", "月明かりの階段", "眠れない空"],
    "fire": ["火花の散る暗がり", "燃えさしみたいな息", "余熱の残る掌"],
    "darkness": ["灯りの届かない水面", "暗がりの端", "影だけが伸びる壁際"],
    "tension": ["警報みたいに静かな廊下", "張りつめた空気の隙間", "息をひそめる改札前"],
}

GENERIC_SCENES = [
    "真夜中の交差点",
    "眠れないままの部屋",
    "朝の輪郭",
    "高架下の湿った影",
]

CONDITIONING_TERM_NORMALIZATION = {
    "heartbeat": "脈拍",
    "pulse": "鼓動",
    "zigzag": "脈の乱れ",
    "chart": "カルテ",
    "medical chart": "カルテ",
    "medical charts": "カルテ",
    "scalpel": "メス",
    "medication": "投薬",
    "diagnosis": "診断",
    "error": "誤差",
    "tears": "涙",
    "forbidden tears": "禁じた涙",
    "judgment": "裁き",
    "separation": "断絶",
    "whisper": "囁き",
    "vulnerability": "脆さ",
    "emotion": "感情",
    "emotions": "感情",
    "soul": "心",
    "heart": "心",
    "messy emotions": "乱れた感情",
    "logical diagnosis": "論理の診断",
    "irrational tears": "不合理な涙",
    "medical analysis of the soul": "心の診断",
}

CONDITIONING_AXIS_KEYWORDS = {
    "defiance": ["rebellion", "anti-conformity", "defiance", "heroism", "aggression", "challenger", "reject", "strongest"],
    "uplift": ["liberation", "utopia", "hope", "changing the world", "rising", "heroic", "radiant", "world-opening"],
    "light": ["magic", "sparkle", "shimmer", "radiant", "light", "backlight", "new world"],
    "darkness": ["destruction", "curse", "apocalyptic", "monstrous", "ruin", "forbidden", "rage"],
    "night": ["night", "urban night", "late night", "dance party", "festival energy"],
    "noise": ["chaos", "shouting", "festival", "collective dance", "loud", "screaming"],
    "motion": ["dance", "drive", "rising", "forward motion", "escape", "escape guide", "opening doors"],
    "tension": ["pain", "frustration", "tears", "wounded", "shaking", "internal screaming", "pressure"],
    "fire": ["fireworks", "fire", "explosive", "flame", "big bang", "burn", "burning"],
}

CONDITIONING_EMOTION_KEYWORDS = {
    "defiance": ["rebellion", "anti-conformity", "defiance", "heroism", "aggression", "reject", "strongest"],
    "vulnerability": ["self-loathing", "pain", "tears", "wounded", "frustration", "weakness"],
    "uplift": ["hope", "liberation", "utopia", "radiant", "heroic", "changing the world"],
    "tension": ["chaos", "rage", "curse", "apocalyptic", "pressure", "screaming"],
    "motion": ["dance", "drive", "rising", "forward motion", "escape"],
}

EMOTION_STATEMENTS = {
    "uplift": [
        "まだ行けると息が言った",
        "追い風を信じる余白が残っていた",
        "落ちきらない光を拾っていた",
    ],
    "vulnerability": [
        "うまく言えないまま立ち尽くした",
        "隠しきれない本音が揺れていた",
        "弱さだけが先に名前を持った",
    ],
    "motion": [
        "止まれないまま考えていた",
        "足音だけが答えを急がせた",
        "走りながらようやく気づいた",
    ],
    "defiance": [
        "ここで引けないとやっと思えた",
        "折れない息だけは手放せない",
        "黙ったまま終われないと知った",
    ],
    "darkness": [
        "影の深さまで抱えていた",
        "暗がりの底でも消えたくなかった",
        "灯りのない場所でも目を閉じなかった",
    ],
    "tension": [
        "心拍だけが先に尖っていく",
        "息をひそめたまま朝を待った",
        "言い訳より先に鼓動が走った",
    ],
}

TURN_MARKERS = ["それでも", "だけど", "なのに", "だからこそ"]
HOOK_SUFFIXES = ["を離さない", "ごと抱きしめる", "のままで跳ぶ", "を嘘にしない"]
FUTURE_RELEASES = [
    "終われない夜ごと抱いて それでも明日へ踏み出す",
    "ほどけない弱さまで 未来の方へ連れていく",
    "消えない残響ごと ここから先へ運んでいく",
    "言い訳より先に 私たちは次の光へ触れていく",
]


def load_historical_candidates(track_id: str, output_dir: Path, *, limit: int = 8) -> list[dict[str, Any]]:
    project_outputs = Path(__file__).resolve().parents[2] / "outputs"
    parent = output_dir.parent
    if not parent.exists() and not project_outputs.exists():
        return []

    candidates: list[dict[str, Any]] = []
    seen_hashes: set[str] = set()
    seen_dirs: set[Path] = set()
    sibling_dirs = sorted(
        (
            path for path in parent.iterdir()
            if path.is_dir() and path != output_dir and path.name.startswith(track_id)
        ),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    ) if parent.exists() else []

    def try_add_run(run_dir: Path) -> None:
        nonlocal candidates
        if run_dir in seen_dirs or run_dir == output_dir:
            return
        selected_path = run_dir / "selected_lyric.md"
        if not selected_path.exists():
            return
        markdown = selected_path.read_text(encoding="utf-8").strip()
        if not markdown:
            return
        digest = hashlib.md5(markdown.encode("utf-8")).hexdigest()
        if digest in seen_hashes:
            return
        seen_dirs.add(run_dir)
        seen_hashes.add(digest)
        title = next(
            (line[2:].strip() for line in markdown.splitlines() if line.startswith("# ")),
            run_dir.name,
        )
        candidates.append(
            {
                "candidate_id": f"{track_id}-history-{run_dir.name}-{hashlib.md5(str(run_dir.resolve()).encode('utf-8')).hexdigest()[:8]}",
                "variant_index": 0,
                "title": title,
                "markdown": markdown if markdown.endswith("\n") else markdown + "\n",
                "source_run_dir": str(run_dir),
            }
        )

    for sibling in sibling_dirs:
        try_add_run(sibling)
        if len(candidates) >= limit:
            return candidates

    if project_outputs.exists():
        plan_paths = sorted(
            project_outputs.rglob("plan.json"),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
        for plan_path in plan_paths:
            run_dir = plan_path.parent
            if run_dir == output_dir:
                continue
            try:
                plan_payload = json.loads(plan_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if str(plan_payload.get("track_id", "")).strip() != track_id:
                continue
            try_add_run(run_dir)
            if len(candidates) >= limit:
                break
    return candidates


def stable_rng(record: dict[str, Any], *, salt: str) -> random.Random:
    stable_id = record.get("record_id") or record.get("eval_id") or record.get("track_id") or "record"
    seed = int(hashlib.md5(f"{stable_id}:{salt}".encode("utf-8")).hexdigest()[:8], 16)
    return random.Random(seed)


def first_lines(markdown_text: str) -> list[str]:
    lines: list[str] = []
    for _, section_lines in extract_section_blocks(markdown_text):
        if section_lines:
            lines.append(section_lines[0])
    return lines


def dedupe_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: list[dict[str, Any]] = []
    seen_markdown_hashes: set[str] = set()
    seen_candidate_ids: set[str] = set()
    for candidate in candidates:
        markdown = str(candidate.get("markdown", "")).strip()
        if not markdown:
            continue
        digest = hashlib.md5(markdown.encode("utf-8")).hexdigest()
        if digest in seen_markdown_hashes:
            continue
        candidate_id = str(candidate.get("candidate_id", "")).strip() or f"candidate-{len(deduped) + 1}"
        if candidate_id in seen_candidate_ids:
            candidate_id = f"{candidate_id}-{digest[:8]}"
        seen_markdown_hashes.add(digest)
        seen_candidate_ids.add(candidate_id)
        if candidate_id != candidate.get("candidate_id"):
            candidate = {**candidate, "candidate_id": candidate_id}
        deduped.append(candidate)
    return deduped


def perspective_for_record(record: dict[str, Any]) -> str:
    language_profile = record.get("input_context", {}).get("track_evidence", {}).get("language_profile", {})
    dominant = str(language_profile.get("dominant_perspective", "")).strip()
    if dominant in {"first_person", "second_person"}:
        return dominant
    if "First-Person" in record.get("input_context", {}).get("artist_context", {}).get("style_tags", []):
        return "first_person"
    return "first_person"


FALLBACK_MOTIF_BANK = {
    "body": ["心拍", "体温", "指先"],
    "noise": ["雑音", "残響", "ざわめき"],
    "time": ["秒針", "真夜中", "明日"],
    "defiance": ["反撃", "牙", "叫び"],
    "light": ["光", "まぶた", "朝焼け"],
    "city": ["ネオン", "路地", "信号"],
    "fracture": ["ひび", "破片", "傷口"],
    "vulnerability": ["本音", "涙", "素肌"],
    "motion": ["走る", "揺れる", "跳ねる"],
    "uplift": ["浮上", "跳躍", "呼吸"],
    "weather": ["霧", "風", "雨粒"],
    "night": ["夜", "月影", "真夜中"],
    "fire": ["火花", "熱", "炎"],
    "darkness": ["影", "暗闇", "黒"],
    "tension": ["鼓動", "緊張", "息継ぎ"],
}

FALLBACK_SCENE_BANK = {
    "body": ["胸の内側", "指先の熱", "息が近い距離"],
    "noise": ["雑踏のすき間", "ノイズの残る部屋", "耳鳴りのする交差点"],
    "time": ["秒針の隙間", "真夜中の手前", "明日の輪郭"],
    "defiance": ["噛みしめた夜", "折れない喉", "踏み返す足元"],
    "light": ["光の手前", "朝焼けの窓", "ほどける明かり"],
    "city": ["ネオンの路地", "信号の下", "眠らない街角"],
    "fracture": ["ひび割れた鏡", "割れた街灯", "裂け目のある夜"],
    "vulnerability": ["言えない本音の部屋", "濡れたまぶた", "素肌の記憶"],
    "motion": ["走り抜ける道路", "浮力だけが残る夜空", "揺れ続ける電車窓"],
    "uplift": ["息を吸い直す朝", "開きかけた空", "跳び越える瞬間"],
    "weather": ["霧のホーム", "風の抜ける屋上", "雨粒の残る街"],
    "night": ["深夜の歩道橋", "月の薄い帰り道", "眠れない窓辺"],
    "fire": ["火花の散る視界", "熱の残る掌", "焦げるような呼吸"],
    "darkness": ["暗闇の階段", "影だけ伸びる廊下", "黒い水面"],
    "tension": ["張りつめた踊り場", "息を止める手前", "触れそうで触れない距離"],
}

CLEAN_GENERIC_SCENES = ["真夜中の手前", "胸の内側", "ネオンの路地", "息を吸い直す朝"]




def conditioning_record_is_usable_for_generation(conditioning: dict[str, Any]) -> bool:
    identity = conditioning.get("track_identity", {})
    lyric_ground_truth = conditioning.get("lyric_ground_truth", {})
    section_analysis = conditioning.get("section_analysis", [])
    quality_control = conditioning.get("quality_control", {})

    if not quality_control.get("ready_for_prompting", False):
        return False

    title = identity.get("title", "")
    if looks_corrupted_text(title):
        return False

    hook_lines = lyric_ground_truth.get("hook_lines", [])
    section_lines: list[str] = []
    for section in lyric_ground_truth.get("sections", []):
        section_lines.extend(section.get("lines", []))

    probe_texts = [title, *hook_lines[:3], *section_lines[:6]]
    meaningful_count = sum(1 for item in probe_texts if is_safe_lyric_term(str(item)))
    corrupted_count = sum(1 for item in probe_texts if looks_corrupted_text(item))

    if meaningful_count < 3:
        return False
    if corrupted_count >= max(2, len([item for item in probe_texts if str(item).strip()]) // 2):
        return False
    if len(section_analysis) < 3:
        return False
    return True


def safe_prompt_terms(terms: list[str], fallback: list[str]) -> list[str]:
    cleaned = [str(term).strip() for term in terms if is_safe_prompt_term(str(term))]
    cleaned = unique_preserve_order(cleaned)
    if cleaned:
        return cleaned
    return unique_preserve_order(fallback)


def voice_bundle(record: dict[str, Any], rng: random.Random) -> dict[str, str]:
    perspective = perspective_for_record(record)
    if perspective == "second_person":
        return {"voice": "私", "address": "あなた"}
    return {"voice": rng.choice(["私", "僕"]), "address": rng.choice(["君", "あなた", "名前のない誰か"])}


def motif_roster(record: dict[str, Any], rng: random.Random) -> list[dict[str, Any]]:
    axes = resolved_theme_axes_for_record(record)
    imagery = style_imagery_bank(record)
    roster: list[dict[str, Any]] = []
    for axis in axes:
        pool = unique_preserve_order(THEME_BANK.get(axis, []) + imagery)
        shuffled = pool[:]
        rng.shuffle(shuffled)
        roster.append(
            {
                "axis": axis,
                "motifs": shuffled[:3],
                "scene_candidates": THEME_SCENES.get(axis, [])[:3],
            }
        )
    return roster


def narrative_beats(record: dict[str, Any], rng: random.Random) -> dict[str, str]:
    axes = resolved_theme_axes_for_record(record)
    emotions = resolved_dominant_emotions_for_record(record)
    statements = []
    for emotion in emotions:
        statements.extend(EMOTION_STATEMENTS.get(emotion, []))
    if not statements:
        statements = EMOTION_STATEMENTS["vulnerability"] + EMOTION_STATEMENTS["motion"]

    opening = rng.choice(statements)
    pressure = rng.choice(EMOTION_STATEMENTS.get("tension", EMOTION_STATEMENTS["vulnerability"]))
    if "defiance" in axes:
        turn = rng.choice(EMOTION_STATEMENTS["defiance"])
    elif "uplift" in axes:
        turn = rng.choice(EMOTION_STATEMENTS["uplift"])
    else:
        turn = rng.choice(statements)
    release = rng.choice(FUTURE_RELEASES)
    return {
        "opening_state": opening,
        "pressure_point": pressure,
        "turn_point": turn,
        "release_point": release,
    }


def release_markers_for_axes(theme_axes: list[str]) -> list[str]:
    markers = ["ここから", "明日", "未来", "踏み出す", "連れていく", "連れてくる", "越えて", "変えて"]
    if "uplift" in theme_axes or "light" in theme_axes:
        markers.extend(["開く", "照らす", "飛ぶ"])
    if "defiance" in theme_axes or "fracture" in theme_axes:
        markers.extend(["裂く", "逸らさない", "離さない"])
    if "vulnerability" in theme_axes:
        markers.extend(["抱えて", "信じる", "ほどける"])
    return unique_preserve_order(markers)


MODE_JP_BANKS = {
    "ironic_meta": {
        "title_roots": ["ラベル", "神話もどき", "匿名熱", "模造神", "仮面語", "残ったタグ"],
        "hook_prefixes": ["それ", "また", "ほら", "もう", "だって"],
        "hook_verbs": ["バレてる", "透けてる", "余ってる", "滑ってる", "騙ってる"],
        "appeal_verbs": ["言い切ってよ", "見抜いてよ", "笑ってよ", "暴いてよ"],
        "decisions": ["正体ごと晒していく", "うわべのまま終わらない", "ラベル越しに言い返す", "神話もどきでも噛みつく"],
        "release_words": ["借り物のままでも", "薄っぺらでも", "見透かされても", "笑われながらでも"],
        "pressure_words": ["借りた言葉", "空っぽの権威", "軽い神格化", "安い偶像"],
        "outro_words": ["タグ", "残響", "借り物", "見抜かれた顔"]
    },
    "direct_emotional_pop": {
        "title_roots": ["さよなら未満", "体温差", "愛の途中", "まだ好き", "言えない熱", "残る声"],
        "hook_prefixes": ["ねえ", "まだ", "きっと", "どうして", "今も"],
        "hook_verbs": ["離れない", "消えない", "届かない", "戻れない", "言えない"],
        "appeal_verbs": ["抱きしめてよ", "聞いてよ", "振り向いてよ", "連れていってよ"],
        "decisions": ["痛いままで抱えていく", "好きなまま引き返さない", "言えないままでも進む", "壊れても手放さない"],
        "release_words": ["泣きながらでも", "寂しいままでも", "ほどけなくても", "最後まで"],
        "pressure_words": ["浅い呼吸", "濡れた声", "熱の残り", "言えない鼓動"],
        "outro_words": ["体温", "余熱", "残る声", "まだ好き"]
    },
    "dark_cute_breakdown": {
        "title_roots": ["砂糖毒", "割れたリボン", "甘い破片", "魔法の残骸", "かわいい罠", "歪んだショコラ"],
        "hook_prefixes": ["ほら", "もっと", "まだ", "だって", "こんなに"],
        "hook_verbs": ["壊れる", "甘すぎる", "刺さってる", "終われない", "笑ってる"],
        "appeal_verbs": ["噛み砕いてよ", "かわいがってよ", "壊してよ", "見逃さないで"],
        "decisions": ["甘いままで裂いていく", "かわいい顔で噛みつく", "毒ごと飲み干していく", "壊れたまま踊り切る"],
        "release_words": ["砂糖のままでも", "ぐちゃぐちゃでも", "かわいくても", "痛みごとでも"],
        "pressure_words": ["甘いノイズ", "割れたリボン", "笑う毒", "にじむメイク"],
        "outro_words": ["残り香", "割れた飾り", "甘い傷", "笑い声"]
    },
    "intimate_confessional": {
        "title_roots": ["脈", "傷口", "白いノイズ", "喉の奥", "ひび", "残響"],
        "hook_prefixes": ["まだ", "それでも", "うるさい", "知るか", "ここで"],
        "hook_verbs": ["鳴ってる", "消えない", "折れない", "終われない", "離さない"],
        "appeal_verbs": ["暴いてよ", "ほどいてよ", "言い当ててよ", "見逃さないで"],
        "decisions": ["それでも行く", "傷ごと抱えていく", "まだ言い切る", "ここで終わらせない", "黙ったまま進む"],
        "release_words": ["壊れたままでも", "綺麗じゃなくても", "夜の底でも", "息を切らしても"],
        "pressure_words": ["噛みしめた声", "浅い呼吸", "遅れた鼓動", "黙れない痛み"],
        "outro_words": ["傷あと", "余熱", "残り火", "体温"],
    },
    "night_drive": {
        "title_roots": ["ネオン", "午前二時", "交差点", "滑走", "信号", "夜景"],
        "hook_prefixes": ["もっと", "今夜", "行け", "まだ", "飛ばせ"],
        "hook_verbs": ["加速する", "消えない", "抜けていく", "止まらない", "走ってる"],
        "appeal_verbs": ["見逃さないで", "振り切ってよ", "追い越してよ", "置いていかないで"],
        "decisions": ["ブレーキは捨てる", "夜を突き抜ける", "もう振り返らない", "最後まで走る", "朝まで切らさない"],
        "release_words": ["濡れた空でも", "街灯の先まで", "速度のままで", "闇を裂いても"],
        "pressure_words": ["跳ねる靴音", "荒い呼吸", "滲むネオン", "軋むスピード"],
        "outro_words": ["街灯", "尾灯", "夜風", "残る速度"],
    },
    "anthemic_cinematic": {
        "title_roots": ["逆光", "光の縁", "発火点", "跳ね返る鼓動", "高い空", "残る火花"],
        "hook_prefixes": ["いま", "行け", "越えろ", "立て", "響け"],
        "hook_verbs": ["開く", "届く", "燃える", "立ち上がる", "放つ"],
        "appeal_verbs": ["照らしてよ", "暴いてよ", "引き上げてよ", "掲げてよ"],
        "decisions": ["この手で越えていく", "最後まで掲げる", "落ちながらでも進む", "終わりまで離さない", "ここから開いていく"],
        "release_words": ["闇の向こうでも", "空の縁まで", "火花ごと", "高い場所へ"],
        "pressure_words": ["張りつめた光", "高鳴る気流", "裂ける雲間", "こぼれる火花"],
        "outro_words": ["残る光", "火花", "余韻", "空の縁"],
    },
}


def mode_jp_bank(mode: str) -> dict[str, list[str]]:
    return MODE_JP_BANKS.get(mode, MODE_JP_BANKS["intimate_confessional"])


def voice_bundle(record: dict[str, Any], rng: random.Random) -> dict[str, str]:
    perspective = perspective_for_record(record)
    if perspective == "second_person":
        return {"voice": "私", "address": "あなた"}
    return {
        "voice": rng.choice(["私", "僕"]),
        "address": rng.choice(["君", "あなた", "名前のない誰か"]),
    }


def motif_roster(record: dict[str, Any], rng: random.Random) -> list[dict[str, Any]]:
    axes = resolved_theme_axes_for_record(record)
    imagery = safe_prompt_terms(style_imagery_bank(record), [])
    
    # Alexandria Integration: Draw inspiration from thousands of high-fidelity tracks
    model_name = record.get("custom_model_cluster", "Model_B_Humanoid_Pop")
    alexandria = _get_alexandria()
    library_motifs = alexandria.get_motifs_for_model(model_name, limit=6)
    library_hint = alexandria.get_structural_hint(model_name)

    roster: list[dict[str, Any]] = []
    for axis in axes:
        # Mix in the Alexandria motifs with the axis-specific pool
        pool = safe_prompt_terms(
            THEME_BANK.get(axis, []) + imagery + library_motifs,
            FALLBACK_MOTIF_BANK.get(axis, FALLBACK_MOTIF_BANK["night"]),
        )
        shuffled = pool[:]
        rng.shuffle(shuffled)
        roster.append(
            {
                "axis": axis,
                "motifs": shuffled[:3],
                "scene_candidates": safe_prompt_terms(
                    THEME_SCENES.get(axis, []),
                    FALLBACK_SCENE_BANK.get(axis, CLEAN_GENERIC_SCENES),
                )[:3],
                "structural_hint": library_hint, # Massive DNA injection
            }
        )
    return roster


def output_contract_for_sections(section_order: list[str]) -> dict[str, Any]:
    ordered_headers = [f"[{section}]" for section in section_order]
    return {
        "title_line": "# <Japanese title>",
        "ordered_headers": ordered_headers,
        "format_rules": [
            "Return markdown lyrics only.",
            "Put the title on the first line with '# '.",
            "Use the section headers exactly as listed and keep the same order.",
            "Do not add commentary, bullet points, or bold title formatting.",
        ],
    }


SECTION_GOAL_DEFAULTS = {
    "intro": "Open on a sharp image or emotional premise before the main movement begins.",
    "chorus_open": "Start with an immediate hook hit, then leave room for the later choruses to grow.",
    "verse_1": "Carry concrete details and perspective-specific storytelling.",
    "verse_1_extension": "Deepen the scene before the first big hook lands.",
    "pre_chorus": "Compress the language and tighten emotion before the chorus release.",
    "chorus": "Deliver the core hook in a chantable, memorable form.",
    "verse_2": "Increase specificity and tension through denser descriptive lines.",
    "pre_chorus_2": "Rebuild pressure faster than the first rise and sharpen the emotional focus.",
    "chorus_2": "Return to the hook with extra force or a changed angle.",
    "interlude": "Suspend the forward motion for a brief image or breath before the next turn.",
    "bridge": "Change angle or emotional framing before the final section.",
    "bridge_rise": "Push the energy upward so the final chorus feels earned.",
    "chorus_final": "Deliver the core hook in a chantable, memorable form. Push the final chorus as the clearest emotional release point.",
    "outro": "Leave a final afterimage instead of explaining the song.",
}

SECTION_LINE_RANGES = {
    "intro": (1, 3),
    "chorus_open": (3, 5),
    "verse_1": (3, 6),
    "verse_1_extension": (2, 4),
    "pre_chorus": (2, 4),
    "chorus": (3, 5),
    "verse_2": (3, 6),
    "pre_chorus_2": (2, 4),
    "chorus_2": (3, 5),
    "interlude": (2, 4),
    "bridge": (2, 4),
    "bridge_rise": (2, 4),
    "chorus_final": (4, 6),
    "outro": (1, 3),
}


def clamp_int(value: int, low: int, high: int) -> int:
    return max(low, min(high, value))


def inferred_section_entries(record: dict[str, Any]) -> list[dict[str, Any]]:
    target_structure = record.get("target", {}).get("track_conditioned_structure", {})
    inferred_form = record.get("input_context", {}).get("track_evidence", {}).get("inferred_song_form", {})
    ordered_sections = target_structure.get("ordered_sections") or inferred_form.get("ordered_sections") or []

    entries: list[dict[str, Any]] = []
    for item in ordered_sections:
        label = str(item.get("inferred_label") or item.get("section") or item.get("source_section") or "").strip()
        if not label:
            continue
        entries.append(
            {
                "label": label,
                "canonical": canonical_section_name(label),
                "line_count": int(item.get("line_count", 0) or 0),
            }
        )
    return entries


def short_line_ratio_for_record(record: dict[str, Any]) -> float:
    ratio = (
        record.get("input_context", {})
        .get("track_evidence", {})
        .get("language_profile", {})
        .get("line_length_profile", {})
        .get("short_line_ratio", 0.0)
    )
    try:
        return float(ratio)
    except (TypeError, ValueError):
        return 0.0


def default_goal_for_section(section: str) -> str:
    canonical = canonical_section_name(section)
    return SECTION_GOAL_DEFAULTS.get(section, SECTION_GOAL_DEFAULTS.get(canonical, "Keep the section purposeful and image-driven."))


def line_range_for_section(section: str) -> tuple[int, int]:
    canonical = canonical_section_name(section)
    return SECTION_LINE_RANGES.get(section, SECTION_LINE_RANGES.get(canonical, (2, 4)))


def observed_line_count_for_section(entries: list[dict[str, Any]], section: str) -> int:
    if not entries:
        return 0

    if section == "chorus_open":
        for entry in entries:
            if entry["canonical"] == "chorus":
                return entry["line_count"]
        return 0

    if section == "chorus_final":
        exact = [entry["line_count"] for entry in entries if entry["label"] == "chorus_final"]
        if exact:
            return round(sum(exact) / len(exact))
        chorus_lines = [entry["line_count"] for entry in entries if entry["canonical"] == "chorus"]
        return chorus_lines[-1] if chorus_lines else 0

    if section in {"chorus", "chorus_2"}:
        chorus_lines = [entry["line_count"] for entry in entries if entry["canonical"] == "chorus" and entry["label"] != "chorus_final"]
        if not chorus_lines:
            return 0
        sample = chorus_lines[:2] if section == "chorus" else (chorus_lines[1:-1] or chorus_lines[1:] or chorus_lines[-2:])
        return round(sum(sample) / len(sample))

    if section in {"pre_chorus", "pre_chorus_2"}:
        pre_lines = [entry["line_count"] for entry in entries if entry["label"].startswith(section)]
        if pre_lines:
            return round(sum(pre_lines) / len(pre_lines))
        canonical_pre = [entry["line_count"] for entry in entries if entry["canonical"] == "pre_chorus"]
        return round(sum(canonical_pre) / len(canonical_pre)) if canonical_pre else 0

    if section == "verse_1_extension":
        extension_lines = [entry["line_count"] for entry in entries if entry["label"].startswith("verse_1_extension")]
        if extension_lines:
            sample = extension_lines[:2]
            return round(sum(sample) / len(sample))
        verse_lines = [entry["line_count"] for entry in entries if entry["canonical"] == "verse_1"]
        return verse_lines[1] if len(verse_lines) > 1 else (verse_lines[0] if verse_lines else 0)

    if section == "bridge_rise":
        rise_lines = [entry["line_count"] for entry in entries if entry["label"].startswith("bridge_rise")]
        if rise_lines:
            return round(sum(rise_lines) / len(rise_lines))
        bridge_lines = [entry["line_count"] for entry in entries if entry["canonical"] == "bridge"]
        return bridge_lines[-1] if bridge_lines else 0

    if section == "interlude":
        interlude_lines = [entry["line_count"] for entry in entries if entry["label"].startswith("interlude")]
        return round(sum(interlude_lines) / len(interlude_lines)) if interlude_lines else 0

    exact = [entry["line_count"] for entry in entries if entry["label"] == section]
    if exact:
        return round(sum(exact) / len(exact))

    canonical = canonical_section_name(section)
    matched = [entry["line_count"] for entry in entries if entry["canonical"] == canonical]
    return round(sum(matched) / len(matched)) if matched else 0


def derive_section_order(record: dict[str, Any]) -> tuple[list[str], list[dict[str, Any]]]:
    recommended = section_plan(record)
    entries = inferred_section_entries(record)
    if not entries:
        return recommended, entries

    labels = [entry["label"] for entry in entries]
    canonicals = [entry["canonical"] or entry["label"] for entry in entries]
    chorus_count = sum(1 for canonical in canonicals if canonical == "chorus")
    starts_with_chorus = bool(canonicals) and canonicals[0] == "chorus"
    has_intro = "intro" in canonicals[:3]
    has_outro = "outro" in canonicals[-3:]
    has_extension = any(label.startswith("verse_1_extension") for label in labels)
    has_pre_chorus = any(canonical == "pre_chorus" for canonical in canonicals)
    has_pre_chorus_2 = any(label.startswith("pre_chorus_2") for label in labels)
    has_verse_2 = any(canonical == "verse_2" for canonical in canonicals)
    has_interlude = any(label.startswith("interlude") for label in labels)
    has_bridge = any(canonical == "bridge" for canonical in canonicals)
    has_bridge_rise = any(label.startswith("bridge_rise") for label in labels)

    section_order: list[str] = []
    if has_intro:
        section_order.append("intro")
    if starts_with_chorus:
        section_order.append("chorus_open")
    if not starts_with_chorus or has_extension or has_verse_2:
        section_order.append("verse_1")
    if has_extension:
        section_order.append("verse_1_extension")
    if has_pre_chorus:
        section_order.append("pre_chorus")
    if not starts_with_chorus or chorus_count > 1:
        section_order.append("chorus")
    if has_verse_2:
        section_order.append("verse_2")
    if has_pre_chorus_2:
        section_order.append("pre_chorus_2")
    if chorus_count >= 4 and (has_interlude or has_bridge or has_bridge_rise):
        section_order.append("chorus_2")
    if has_interlude:
        section_order.append("interlude")
    if has_bridge:
        section_order.append("bridge")
    if has_bridge_rise:
        section_order.append("bridge_rise")
    section_order.append("chorus_final")
    if has_outro:
        section_order.append("outro")

    section_order = unique_preserve_order(section_order)
    if len(section_order) < 4 or not any(section.startswith("chorus") for section in section_order):
        return recommended, entries
    return section_order, entries


def form_tags_for_sections(section_order: list[str]) -> list[str]:
    tags: list[str] = []
    if section_order and section_order[0] == "chorus_open":
        tags.append("chorus_open")
    if "verse_1_extension" in section_order:
        tags.append("extended_lead_in")
    if "pre_chorus_2" in section_order:
        tags.append("return_pre_chorus")
    if "interlude" in section_order:
        tags.append("interlude_break")
    if "bridge" in section_order and "bridge_rise" in section_order:
        tags.append("bridge_lift")
    elif "bridge" in section_order:
        tags.append("bridge_turn")
    if "outro" in section_order:
        tags.append("tag_outro")
    if sum(1 for section in section_order if section.startswith("chorus")) >= 3:
        tags.append("multi_wave_hooking")
    return tags or ["core_pop_arc"]


def section_scene(section: str, primary_scene: str, secondary_scene: str, tertiary_scene: str) -> str:
    canonical = canonical_section_name(section)
    if section in {"chorus_open", "chorus", "chorus_2"}:
        return secondary_scene
    if section in {"bridge", "bridge_rise", "interlude", "chorus_final", "outro"}:
        return tertiary_scene
    if canonical in {"chorus", "bridge", "outro"}:
        return tertiary_scene if canonical != "chorus" else secondary_scene
    return primary_scene


def derive_line_target(record: dict[str, Any], section: str, entries: list[dict[str, Any]], rng: random.Random) -> int:
    low, high = line_range_for_section(section)
    observed = observed_line_count_for_section(entries, section)
    canonical = canonical_section_name(section)
    short_ratio = short_line_ratio_for_record(record)

    if observed:
        expansion = 2 if canonical in {"verse_1", "verse_2", "chorus"} else 1
        if section in {"chorus_final", "chorus_2"}:
            expansion = 2
        target = observed + expansion
    else:
        midpoint = round((low + high) / 2)
        target = midpoint + rng.choice([-1, 0, 1])

    if short_ratio >= 0.8 and section in {"verse_1", "verse_1_extension", "chorus", "chorus_2", "chorus_final", "verse_2"}:
        target += 1

    return clamp_int(target, low, high)


def resolve_structure_template(
    record: dict[str, Any],
    entries: list[dict[str, Any]],
    rng: random.Random,
    *,
    mode_id: str | None = None,
) -> dict[str, Any]:
    artist_id = str(record.get("artist_id", "")).strip()
    resolved_mode_id = str(mode_id or record.get("target", {}).get("primary_mode", "")).strip()
    profile = load_structure_profile(artist_id)

    if profile:
        mode_template = dict(profile.get("mode_structures", {}).get(resolved_mode_id, {}))
        section_order = [str(section).strip() for section in mode_template.get("section_order", []) if str(section).strip()]
        if section_order:
            raw_targets = dict(mode_template.get("line_targets", {}))
            line_targets = {
                section: clamp_int(
                    int(raw_targets.get(section, derive_line_target(record, section, entries, rng))),
                    *line_range_for_section(section),
                )
                for section in section_order
            }
            return {
                "source": "structure_profile",
                "section_order": section_order,
                "line_targets": line_targets,
                "form_tags": list(mode_template.get("form_tags", form_tags_for_sections(section_order))),
                "goal_overrides": dict(mode_template.get("goal_overrides", {})),
                "delivery_overrides": dict(mode_template.get("delivery_overrides", {})),
            }

    section_order, _ = derive_section_order(record)
    if not section_order:
        blueprint = get_universal_blueprint()
        section_order = blueprint.universal_section_order
        
    return {
        "source": "mastery_blueprint_fallback",
        "section_order": section_order,
        "line_targets": {
            section: derive_line_target(record, section, entries, rng)
            for section in section_order
        },
        "form_tags": form_tags_for_sections(section_order),
        "goal_overrides": {},
        "delivery_overrides": {},
    }


def build_song_plan(record: dict[str, Any]) -> dict[str, Any]:
    rng = stable_rng(record, salt="plan")
    artist_id = str(record.get("artist_id", "")).strip()
    artist_profile = load_artist_profile(artist_id) or {}
    title = str(record.get("title", "")).split("(")[0].strip() or str(record.get("track_id"))
    conditioning = matching_conditioning_record(record)
    if conditioning and not conditioning_record_is_usable_for_generation(conditioning):
        conditioning = None
    primary_mode, mode_source = resolve_primary_mode(record, conditioning)
    mode_support_context = load_mode_support_context(
        project_root(),
        primary_mode,
        current_track_id=str(record.get("track_id", "")).strip(),
    )
    mode_support_enabled = support_enabled_for_record(record, conditioning)
    if not mode_support_enabled:
        mode_support_context = {"available": False, "mode_id": primary_mode, "records": []}
    conditioning_hints = build_conditioning_section_hints(conditioning) if conditioning else {}
    conditioning_hook_terms = conditioning_hook_atoms(conditioning) if conditioning else []
    conditioning_title_terms = conditioning_title_atoms(conditioning) if conditioning else []
    conditioning_contrast = conditioning_contrast_terms(conditioning) if conditioning else []
    conditioning_hook_style = detect_conditioning_hook_style(conditioning) if conditioning else {
        "question_driven": False,
        "appeal_mode": False,
        "chant_mode": False,
        "question_heads": [],
    }
    direct_emotional_profile = ""
    if primary_mode == "direct_emotional_pop" and conditioning:
        direct_emotional_profile = detect_direct_emotional_profile(
            {
                "source_lines": conditioning_hook_lines(conditioning),
                "required_motifs": conditioning_hook_terms + conditioning_title_terms,
            },
            track_id=str(conditioning.get("track_identity", {}).get("track_id", "")).strip(),
        )
        if direct_emotional_profile:
            conditioning_hook_terms = compact_direct_emotional_motifs(
                direct_emotional_profile,
                conditioning_hook_terms + conditioning_title_terms,
            )
            conditioning_title_terms = compact_direct_emotional_motifs(
                direct_emotional_profile,
                conditioning_title_terms,
            )
    voices = voice_bundle(record, rng)
    theme_axes = resolved_theme_axes_for_record(record)
    if conditioning:
        theme_axes = conditioning_theme_axes(conditioning, theme_axes)
    if mode_support_context.get("available"):
        theme_axes = unique_preserve_order(theme_axes + list(mode_support_context.get("theme_axes", [])))[:5]
    roster = conditioning_motif_roster(conditioning, theme_axes, rng) if conditioning else None
    if not roster:
        roster = motif_roster(record, rng)
    if mode_support_context.get("available"):
        roster = merge_mode_support_roster(roster, mode_support_context)
    mode_bank = mode_jp_bank(primary_mode)
    artist_context = record.get("input_context", {}).get("artist_context", {})
    section_order, inferred_entries = derive_section_order(record)
    structure_template = resolve_structure_template(record, inferred_entries, rng, mode_id=primary_mode)
    section_order = structure_template["section_order"]
    goals = section_goals(record)
    dominant_emotions = resolved_dominant_emotions_for_record(record)
    if conditioning:
        dominant_emotions = conditioning_dominant_emotions(conditioning, dominant_emotions)
    beats = narrative_beats(
        {
            **record,
            "_override_theme_axes": theme_axes,
            "_override_dominant_emotions": dominant_emotions,
        },
        rng,
    )
    output_contract = output_contract_for_sections(section_order)
    force_glitch_intensity = record.get("force_glitch_intensity", 0.0)

    scenes = []
    for item in roster:
        scenes.extend(item.get("scene_candidates", []))
    scenes = unique_preserve_order(scenes) or GENERIC_SCENES
    primary_scene = rng.choice(scenes)
    secondary_scene = rng.choice([scene for scene in scenes if scene != primary_scene] or GENERIC_SCENES)
    tertiary_scene = rng.choice([scene for scene in scenes if scene not in {primary_scene, secondary_scene}] or [secondary_scene, primary_scene])
    if not is_safe_prompt_term(primary_scene):
        primary_scene = rng.choice(CLEAN_GENERIC_SCENES)
    if not is_safe_prompt_term(secondary_scene):
        secondary_scene = rng.choice([scene for scene in CLEAN_GENERIC_SCENES if scene != primary_scene] or CLEAN_GENERIC_SCENES)
    if not is_safe_prompt_term(tertiary_scene):
        tertiary_scene = rng.choice([scene for scene in CLEAN_GENERIC_SCENES if scene not in {primary_scene, secondary_scene}] or CLEAN_GENERIC_SCENES)

    hook_core = rng.choice([motif for item in roster[:3] for motif in item.get("motifs", []) if motif] or ["夜"])
    if conditioning:
        hook_text, hook_core = conditioning_hook_text(
            conditioning,
            mode_bank=mode_bank,
            fallback_core=hook_core,
            rng=rng,
        )
        if direct_emotional_profile:
            compact_hooks = compact_direct_emotional_hook_lines(
                direct_emotional_profile,
                hook_core,
                conditioning_hook_lines(conditioning),
            )
            if compact_hooks:
                hook_text = compact_hooks[0]
                hook_core = compact_hooks[0]
    else:
        hook_text = f"{rng.choice(mode_bank['hook_prefixes'])}{hook_core}は{rng.choice(mode_bank['hook_verbs'])}"
    if not is_safe_prompt_term(hook_core):
        hook_core = "夜"
        hook_text = f"{rng.choice(mode_bank['hook_prefixes'])}夜は{rng.choice(mode_bank['hook_verbs'])}"

    section_cards = []
    for idx, section in enumerate(section_order, start=1):
        canonical = canonical_section_name(section)
        motif_pool = []
        for item in roster[max(0, idx - 2): idx + 1]:
            motif_pool.extend(item.get("motifs", []))
        motif_pool = unique_preserve_order(motif_pool)[:4]
        conditioning_hint = conditioning_hints.get(section, {})
        section_cards.append(
            {
                "section": section,
                "canonical_section": canonical,
                "goal": (
                    conditioning_hint.get("goal")
                    or structure_template["goal_overrides"].get(section)
                    or goals.get(section)
                    or default_goal_for_section(section)
                ),
                "scene": conditioning_hint.get("scene") or section_scene(section, primary_scene, secondary_scene, tertiary_scene),
                "required_motifs": unique_preserve_order(
                    list(conditioning_hint.get("required_motifs", []))
                    + motif_pool
                    + (list(mode_support_context.get("motif_atoms", []))[:1] if mode_support_context.get("available") else [])
                )[:4],
                "conditioning_atoms": unique_preserve_order(
                    list(conditioning_hint.get("conditioning_atoms", []))
                    + list(conditioning_hint.get("required_motifs", []))
                    + motif_pool
                    + (list(mode_support_context.get("imagery_anchors", []))[:2] if mode_support_context.get("available") else [])
                )[:6],
                "source_atoms": list(conditioning_hint.get("source_atoms", [])),
                "source_lines": list(conditioning_hint.get("source_lines", [])),
                "question_heads": list(conditioning_hint.get("question_heads", [])),
                "has_questions": bool(conditioning_hint.get("has_questions")),
                "emotion_focus": dominant_emotions[:2],
                "line_target": structure_template["line_targets"][section],
                "delivery": conditioning_hint.get("delivery") or structure_template["delivery_overrides"].get(
                    section,
                    (
                        "hook-first"
                        if section.startswith("chorus")
                        else "lift"
                        if section in {"pre_chorus_2", "bridge_rise"}
                        else "suspended"
                        if section == "interlude"
                        else "narrative"
                    ),
                ),
            }
        )

    chorus_target = next((card["line_target"] for card in section_cards if card["section"] == "chorus"), 0)
    for card in section_cards:
        if card["section"] == "chorus_final":
            low, high = line_range_for_section("chorus_final")
            card["line_target"] = clamp_int(max(card["line_target"], chorus_target + 1, 4), low, high)
            break

    if direct_emotional_profile:
        direct_track_id = str(conditioning.get("track_identity", {}).get("track_id", "")).strip() if conditioning else ""
        preserve_section_atoms = direct_track_id in DIRECT_EMOTIONAL_HARD_CASE_TRACKS
        track_specific_seeds = direct_emotional_track_seed_terms(
            direct_track_id,
            direct_emotional_profile,
        )
        profile_seeds = unique_preserve_order(
            track_specific_seeds + direct_emotional_motif_seeds(direct_emotional_profile)
        )
        for card in section_cards:
            section_name = str(card.get("section", "")).strip()
            source_seed_terms = [
                item
                for item in unique_preserve_order(
                    list(card.get("source_atoms", [])) + list(card.get("conditioning_atoms", []))
                )
                if is_safe_lyric_term(item)
            ]
            if preserve_section_atoms and section_name.startswith("chorus"):
                required_seed_terms = source_seed_terms[:2] + conditioning_hook_terms[:1] + conditioning_title_terms[:1] + profile_seeds[:1]
            elif preserve_section_atoms and section_name.startswith("pre_chorus"):
                required_seed_terms = source_seed_terms[:3] + conditioning_title_terms[:1]
            elif preserve_section_atoms and section_name in {"bridge", "outro"}:
                required_seed_terms = source_seed_terms[-3:] + conditioning_title_terms[:1]
            elif preserve_section_atoms:
                required_seed_terms = source_seed_terms[:4]
            elif section_name.startswith("chorus"):
                required_seed_terms = conditioning_hook_terms + conditioning_title_terms + profile_seeds
            elif section_name.startswith("pre_chorus"):
                required_seed_terms = source_seed_terms[:2] + conditioning_title_terms[:1] + profile_seeds[:1]
            elif section_name in {"bridge", "outro"}:
                required_seed_terms = source_seed_terms[-2:] + conditioning_title_terms[:1] + profile_seeds[:1]
            else:
                required_seed_terms = source_seed_terms[:3] + profile_seeds[:1]
            compact_required = unique_preserve_order(
                [item for item in required_seed_terms + list(card.get("required_motifs", [])) if is_safe_lyric_term(item)]
            )
            compact_atoms = compact_direct_emotional_motifs(
                direct_emotional_profile,
                source_seed_terms + profile_seeds + list(card.get("conditioning_atoms", [])),
            )
            if compact_required:
                card["required_motifs"] = compact_required[:4]
            if compact_atoms:
                if preserve_section_atoms:
                    card["conditioning_atoms"] = unique_preserve_order(source_seed_terms[:3] + compact_atoms)[:6]
                else:
                    card["conditioning_atoms"] = compact_atoms[:6]

    required_new_images = unique_preserve_order(
        [
            *next(
                (
                    card.get("required_motifs", [])
                    for card in section_cards
                    if card.get("section") == "chorus_final"
                ),
                [],
            ),
            tertiary_scene,
        ]
    )[:4]
    if direct_emotional_profile:
        required_new_images = compact_direct_emotional_motifs(direct_emotional_profile, required_new_images)[:4]

    return {
        "schema_version": "1.0",
        "artist_id": record.get("artist_id"),
        "artist_name": record.get("artist_name"),
        "track_id": record.get("track_id"),
        "source_record_id": record.get("record_id"),
        "title_seed": title,
        "primary_mode": primary_mode,
        "mode_source": mode_source,
        "arc_label": arc_label_for_record(record),
        "hook_density": hook_density_for_record(record),
        "voice": voices,
        "style_frame": {
            "summary": artist_context.get("summary", ""),
            "style_tags": artist_context.get("style_tags", []),
            "core_themes": artist_context.get("core_themes", []),
            "imagery_bank": artist_context.get("imagery_bank", []),
        },
        "mode_support_context": mode_support_context,
        "form_profile": {
            "section_order": section_order,
            "tags": structure_template["form_tags"],
            "target_line_total": sum(card["line_target"] for card in section_cards),
            "source_section_count": len(inferred_entries),
            "structure_source": structure_template["source"],
        },
        "artist_profile": artist_profile,
        "theme_axes": theme_axes,
        "dominant_emotions": dominant_emotions,
        "motif_roster": roster,
        "narrative_beats": beats,
        "force_glitch_intensity": force_glitch_intensity,
        "hook_blueprint": {
            "core_text": hook_text,
            "source_atoms": conditioning_hook_terms[:4],
            "repetition_target": "2x in chorus" if hook_density_for_record(record) == "high" else "1-2x",
            "contrast_goal": "chorus should release more clearly than verse",
        },
        "conditioning_context": {
            "available": bool(conditioning),
            "track_id": conditioning.get("track_identity", {}).get("track_id") if conditioning else None,
            "title_core": conditioning.get("track_identity", {}).get("title_core") if conditioning else None,
            "title_jp": conditioning.get("track_identity", {}).get("title") if conditioning else None,
            "title_atoms": conditioning_title_terms,
            "hook_atoms": conditioning_hook_terms,
            "hook_lines": [compact_conditioning_hook_phrase(line) for line in conditioning_hook_lines(conditioning)] if conditioning else [],
            "contrast_terms": conditioning_contrast,
            "hook_shape": conditioning_hook_style,
            "hook_copy_force": conditioning.get("japanese_lyric_profile", {}).get("hook_copy_force") if conditioning else None,
            "title_ignition_style": conditioning.get("japanese_lyric_profile", {}).get("title_ignition_style") if conditioning else None,
            "phrase_source_types": conditioning.get("japanese_lyric_profile", {}).get("phrase_source_types", []) if conditioning else [],
            "critic_focus": conditioning.get("japanese_lyric_profile", {}).get("critic_focus", []) if conditioning else [],
            "contrast_device": conditioning.get("song_intent", {}).get("contrast_device", []) if conditioning else [],
            "dramatic_arc": conditioning.get("song_intent", {}).get("dramatic_arc", []) if conditioning else [],
        },
        "final_release_requirements": {
            "must_be_clearer_than_chorus": True,
            "must_introduce_forward_motion": True,
            "must_add_one_new_image": True,
            "release_markers": unique_preserve_order(
                release_markers_for_axes(theme_axes)
                + list(mode_bank.get("release_words", []))[:3]
                + list(mode_bank.get("decisions", []))[:2]
            ),
            "required_new_images": required_new_images,
        },
        "section_cards": section_cards,
        "output_contract": output_contract,
        "constraints": {
            "language": "Japanese",
            "safety": [
                "No direct artist naming",
                "No lyric reuse from the corpus",
                "Original wording only",
            ],
            "avoid": [
                "flat section energy",
                "English-heavy wording",
                "copying source lyrics",
            ],
        },
    }


def render_generator_prompt(plan: dict[str, Any]) -> str:
    motif_lines = []
    # Removed literal motif roster constraint to allow original metaphorical generation
    section_lines = []
    for card in plan["section_cards"]:
        line = (
            f"- {card['section']}: goal={card['goal'] or card['canonical_section']}, "
            f"scene={card['scene']}, "
            f"target_lines={card['line_target']}, delivery={card['delivery']}"
        )
        if card.get("required_imagery"):
            line += f"\n  [MANDATORY SENSORY ANCHORS: {', '.join(card['required_imagery'])}]"
        section_lines.append(line)
    output_contract = plan["output_contract"]
    final_release = plan["final_release_requirements"]
    form_profile = plan.get("form_profile", {})
    conditioning_context = plan.get("conditioning_context", {})
    mode_support_context = plan.get("mode_support_context", {})
    conditioning_lines: list[str] = []
    if conditioning_context.get("available"):
        if conditioning_context.get("contrast_device"):
            conditioning_lines.append(f"- Contrast device: {', '.join(conditioning_context['contrast_device'][:3])}")
        if conditioning_context.get("dramatic_arc"):
            conditioning_lines.append(f"- Dramatic arc evidence: {', '.join(conditioning_context['dramatic_arc'][:4])}")
        if conditioning_context.get("phrase_source_types"):
            conditioning_lines.append(f"- Phrase source types: {', '.join(conditioning_context['phrase_source_types'])}")
        if conditioning_context.get("hook_copy_force"):
            conditioning_lines.append(f"- Hook copy force target: {conditioning_context['hook_copy_force']}")
        if conditioning_context.get("title_ignition_style"):
            conditioning_lines.append(f"- Title ignition style: {conditioning_context['title_ignition_style']}")
    support_lines: list[str] = []
    if mode_support_context.get("available"):
        if mode_support_context.get("track_ids"):
            support_lines.append(f"- Support tracks: {', '.join(mode_support_context['track_ids'][:3])}")
        if mode_support_context.get("imagery_anchors"):
            support_lines.append(f"- Shared imagery anchors: {', '.join(mode_support_context['imagery_anchors'][:5])}")
        if mode_support_context.get("vocal_tones"):
            support_lines.append(f"- Shared vocal tones: {', '.join(mode_support_context['vocal_tones'][:4])}")
        if mode_support_context.get("production_palette"):
            support_lines.append(f"- Shared production palette: {', '.join(mode_support_context['production_palette'][:4])}")

    artist_profile = plan.get("artist_profile", {})
    lyric_rules = artist_profile.get("lyric_rules", {})
    writing_principles = lyric_rules.get("writing_principles", [])
    stylistic_nuances = lyric_rules.get("stylistic_nuances", {})
    nuance_principles = stylistic_nuances.get("principles", [])
    sfx_triggers = lyric_rules.get("musical_dynamics", {}).get("sfx_triggers", [])

    return "\n".join(
        [
            "Write original Japanese lyrics from this plan.",
            "Output contract:",
            *[f"- {rule}" for rule in output_contract["format_rules"]],
            f"- Required title format: {output_contract['title_line']}",
            f"- Required section order: {' '.join(output_contract['ordered_headers'])}",
            "Stylistic Guidelines:",
            *[f"- {p}" for p in writing_principles],
            *[f"- {p}" for p in nuance_principles],
            *(
                [f"- Musical SFX available: {', '.join(sfx_triggers)}"]
                if sfx_triggers
                else []
            ),
            f"Voice: {plan['voice']['voice']} addressing {plan['voice']['address']}",
            f"Mode: {plan['primary_mode']}",
            f"Arc: {plan['arc_label']}",
            f"Hook core: {plan['hook_blueprint']['core_text']}",
            f"Form tags: {', '.join(form_profile.get('tags', []))}",
            f"Target total lines: {form_profile.get('target_line_total', len(plan['section_cards']) * 4)}",
            *(
                ["Conditioning evidence:"] + conditioning_lines
                if conditioning_lines
                else []
            ),
            *(
                ["Mode support evidence:"] + support_lines
                if support_lines
                else []
            ),
            "Motifs:",
            *motif_lines,
            "Section plan:",
            *section_lines,
            "Final chorus requirements:",
            "- VOCALOID CHARM: Maintain a 'Digital/Vocaloid' texture. Use Katakana for key nouns to create a robotic feel. "
            "Include cute interjections like (Nee?), (Haa?), (Ah), (Uh) to contrast with the clinical horror. "
            "The rhythm should feel like a high-pitched machine-gun delivery.",
            "- chorus_final must feel like a step forward, not a paraphrase of chorus.",
            "- Keep the hook, then add one new concrete image and one irreversible decision or motion line.",
            f"- Prefer at least one release marker from this set: {', '.join(final_release['release_markers'][:8])}",
            f"- If possible, land one of these new images in chorus_final: {', '.join(final_release['required_new_images'][:4])}",
            "Constraints:",
            "- Keep it original and do not quote any existing lyrics.",
            "- Let the final chorus feel more released than the opening verse.",
            "- Prefer concrete images over abstract slogans.",
            "- Respect the short sections as compressed pivots and let the long sections carry specific detail.",
        ]
    )


def render_critic_prompt(plan: dict[str, Any]) -> str:
    conditioning_context = plan.get("conditioning_context", {})
    return "\n".join(
        [
            "Score the lyric against this plan.",
            f"- Required hook density: {plan['hook_density']}",
            f"- Required arc: {plan['arc_label']}",
            *(
                [f"- Japanese critic focus: {', '.join(conditioning_context.get('critic_focus', []))}"]
                if conditioning_context.get("critic_focus")
                else []
            ),
            "- Check motif realization, section contrast, specificity, and repetition control.",
            "- CRITICAL: Look for specific 'Somatic/Mechanical' metaphors (viscera, gears, surgery, files).",
            "- Penalize template-like J-Pop metaphors (stars, wings, sky) if they clash with the artist's dark identity.",
            "- Penalize low density (less than 4 lines per section).",
        ]
    )


def _anonymize_artist_references(text: str) -> str:
    """Replaces explicit artist names with stylistic descriptors to bypass copyright filters."""
    mapping = {
        "maretu": "high-tension chiptune-metal / clinical psychological horror",
        "pinocchiop": "meta-ironic philosophical J-Pop / rapid-fire delivery",
        "kairiki bear": "neurotic phonetic glitch-pop / high-pitched overload",
        "kanaria": "operatic chamber-pop / royal orchestral elegance",
        "deco27": "high-energy punchy rock-pop / relationship cynicism",
        "yoasobi": "literary narrative pop / complex jazz-fusion melodies",
        "syudou": "theatrical cabaret-rock / raw cynical delivery",
    }
    import re
    result = text
    for name, replacement in mapping.items():
        # Case-insensitive replacement
        result = re.sub(re.escape(name), replacement, result, flags=re.IGNORECASE)
    return result


def build_prompt_package(plan: dict[str, Any]) -> dict[str, Any]:
    artist_profile = plan.get("artist_profile", {})
    artist_id = plan.get("artist_id", "")
    vocal_profile = artist_profile.get("vocal_profile", {})
    metadata_header = vocal_profile.get("metadata_header", "").strip()

    demo_plan = plan.get("artist_synthesis_context", {}).get("demo_plan", {})
    archetype_context = demo_plan.get("archetype_context", {})
    artist_sections = archetype_context.get("artist_sections", {})

    def _fuzzy_get(sections: dict[str, str], target: str) -> str:
        for k, v in sections.items():
            if k.strip().lower().startswith(target.lower()):
                return v
        return ""

    identity_block = _fuzzy_get(artist_sections, "Core Identity")
    # Apply Anonymization
    identity_block = _anonymize_artist_references(identity_block)
    
    system_body = (
        "You are a visionary Japanese songwriter working from a structured planning document. "
    )
    if identity_block:
        system_body += f"\nYour Core Identity:\n{identity_block}\n\n"
        
    codex_path = Path(__file__).resolve().parents[2] / "data" / "rules" / "jpop_songwriting_masterclass.md"
    if codex_path.exists():
        masterclass_text = codex_path.read_text(encoding='utf-8')
        
        # 🚨 V3 Architectural Polish: Suspend Mainstream Guardrails for "Grit-Native" Artists
        grit_native_artists = {"hachi", "maretu", "kairiki_bear", "hiragi_kirai", "iyowa"}
        if artist_id in grit_native_artists:
            masterclass_text = masterclass_text.replace(
                "## 🛑 5. Absolute Anti-Cliche / Metaphor-Only Directive",
                "## 🛑 5. [SUSPENDED FOR THIS ARTIST] Absolute Anti-Cliche Directive\n"
                "NOTE: For this specific artist, you ARE ENCOURAGED to use raw, somatically direct words like '傷', '壊す', '狂う', '痛い' if paired with grotesque surrealism. Do not prioritize 'Sophisticated Metaphors' over raw phonetic grit."
            )
        system_body += f"\n{masterclass_text}\n\n"

    # Layer 3: Linguistic Fingerprint Pool — randomly sample 5-6 weapons per run (V3 Expansion)
    # V6 PURE SPIRIT PIVOT: Skip mandatory weapons for Hachi to allow natural poetic flow.
    import random as _lfp_rng
    fingerprint_block = _fuzzy_get(artist_sections, "Linguistic Fingerprint Pool")
    vocabulary_dna = _fuzzy_get(artist_sections, "Lexical DNA")
    phrasing_dna = _fuzzy_get(artist_sections, "Phrasing")

    if fingerprint_block and artist_id != "hachi" and not demo_plan:
        weapon_lines = [line.strip() for line in fingerprint_block.splitlines() if line.strip().startswith("- WEAPON_")]
        if weapon_lines:
            k = min(3, len(weapon_lines)) # Reduced from 6 back to 3 for THEMATIC FOCUS
            selected_weapons = _lfp_rng.sample(weapon_lines, k=k)
            system_body += "\n[MASTERCLASS: ACTIVE LINGUISTIC WEAPONS — MANDATORY INTEGRATION]:\n"
            for weapon in selected_weapons:
                system_body += f"{weapon}\n"
            system_body += "\n"
    
    if vocabulary_dna:
        system_body += f"\n[LEXICAL DNA - Pull your vocabulary ONLY from these fields]:\n{vocabulary_dna}\n"
    if phrasing_dna:
        system_body += f"\n[PHRASING DNA - Match this rhythmic bounce]:\n{phrasing_dna}\n"

    # 🚨 V6 Artist-Specific Persona Enforcement: THE PURE SPIRIT PIVOT
    if artist_id == "hachi":
        system_body += "\n[CREATIVE BRIEF: HACHI (CORE SOUL)]:\n"
        system_body += "- WORLDVIEW: You are Hachi. You observe a world that is decaying, rusted, and filled with the eerie nostalgia of abandoned childhood toys. Everything is analog, tactile, and somatic.\n"
        system_body += "- POETIC INTENT: Do NOT try to match a trope list. Write lines that feel like a distorted memory. Focus on the 'Void' and 'Absence' between people.\n"
        system_body += "- AVOID: Do NOT use digital terms. Do NOT be 'helpful' or 'logical'. If a line feels too safe or clean, break it with a visceral, jagged image.\n"
        system_body += "- LANGUAGE: 100% PURE JAPANESE. No English. No Korean.\n"

    # Layer 4: Iron Scaffold — BPM-aware singability enforcement (V3: Skip for Grit-Native)
    rhythmic_dna = _fuzzy_get(artist_sections, "Rhythmic DNA")
    bpm_match = re.search(r"(\d{2,3})\s*BPM", rhythmic_dna)
    bpm_text = f"{bpm_match.group(1)} BPM" if bpm_match else "dynamic BPM (adjust to genre)"
    
    if artist_id not in {"hachi", "maretu", "kairiki_bear"}:
        system_body += f"\n[IRON SCAFFOLD: MANDATORY SINGABILITY — Tempo: {bpm_text}]:\n"
        system_body += "- Ensure syllable counts are optimized for this tempo.\n"
        system_body += "- Synchronize phrases with standard 4/4 rock beats.\n"
    
    # 🚨 Artist-Sensitive Banned Words: Remove hallmark words from the universal blacklist
    hallmark_imagery = set()
    if demo_plan:
        composite = demo_plan.get("composite_style", {})
        for word in (
            list(composite.get("imagery_anchors", [])) 
            + list(composite.get("seed_phrases", []))
            + list(demo_plan.get("archetype_context", {}).get("artist_sections", {}).get("Common Imagery", "").splitlines())
        ):
            hallmark_imagery.add(str(word).strip())
    
    universal_blacklist = [
        ("嘘", "Lies"), ("痛い", "Pain"), ("大好き", "Love"), ("傷", "Wound"), 
        ("壊れる", "Break"), ("神様", "God"), ("涙", "Tears")
    ]
    active_blacklist = [
        f"{jp}({en})" for jp, en in universal_blacklist 
        if not any(jp in hallmark for hallmark in hallmark_imagery)
    ]
    banned_text = ", ".join(active_blacklist) if active_blacklist else "None (Artist-specific mode active)"
    
    system_body += (
        "\n[IRON SCAFFOLD — ABSOLUTE STRUCTURAL RULES]:\n"
        f"- TARGET TEMPO: ~{bpm_text}. Every line must fit ONE BREATH over this beat.\n"
        "- HARD LINE LENGTH LIMITS (spaces/punctuation excluded):\n"
        "  * Verse/Pre-Chorus lines: 10~18 characters MAX (20 absolute ceiling)\n"
        "  * Chorus/Bridge lines: 8~16 characters MAX (18 absolute ceiling)\n"
        "  * REQUIRED: At least 6-8 lines per Chorus, and 4-6 lines per Verse.\n"
        "  * If a line exceeds the limit, SPLIT IT.\n"
        "- BANNED FORMATS: Essay-like sentences, explanatory clauses, parenthetical translations.\n"
        "- REQUIRED: Short punchy fragments. Conversational stabs. Rhythmic symmetry (7-7, 8-8 mora pairs).\n"
        f"- BANNED VOCABULARY: {banned_text}. Do NOT use literal emotion words.\n"
        "- METAPHOR ANCHOR: You MUST use a Conceptual Metaphor Anchor (e.g., Science, Economics, Machinery, Surgery) to express the theme. Be profoundly poetic, not literally whiny.\n"
        "- Breaking musical structure, exceeding line lengths, or using banned anime cliches is FAILURE.\n"
    )
    if rhythmic_dna:
        system_body += f"- RHYTHMIC DNA CONTEXT: {rhythmic_dna}\n"
    system_body += "\n"


    # Output format — Suno-compatible, hardcoded per user's gold standard
    system_body += (
        "\n[OUTPUT FORMAT — ABSOLUTE REQUIREMENT]:\n"
        "Your output MUST follow this EXACT structure. Any deviation is FAILURE.\n\n"
        "1. START with a plain-text metadata block (Within this block only: NO markdown #, NO brackets):\n"
        "   Genre: <genre description>\n"
        "   Tempo: <BPM and time signature details>\n"
        "   Vocal: <vocal character description>\n"
        "   Instruments: <instrument palette>\n"
        "   Beat Concept: <rhythmic concept in quotes>\n"
        "   Mood & Atmosphere: <emotional atmosphere description>\n"
        "   Theme: <thematic description>\n\n"
        "2. THEN write lyrics with section headers in [Brackets] as required:\n"
        "   [Intro], [Verse 1], [Pre-Chorus], [Chorus], [Verse 2], [Bridge], [Final Chorus], [Outro]\n\n"
        "3. INLINE vocal directions are encouraged: (ah), (uh), (…), (止まらない) etc.\n"
        "4. Use —— dashes for dramatic pauses.\n"
        "5. BANNED: Markdown # headers, English translations, commentary, bullet lists, analysis.\n"
        "6. Write original Japanese lyrics only, never imitate or quote any existing artist.\n"
    )
    if metadata_header:
        system_body += f"\n\nStrictly prefix the output with the following artist metadata header:\n{metadata_header}"

    return {
        "schema_version": "1.0",
        "track_id": plan["track_id"],
        "system_prompt": _anonymize_artist_references(system_body),
        "generator_prompt": _anonymize_artist_references(render_generator_prompt(plan)),
        "critic_prompt": _anonymize_artist_references(render_critic_prompt(plan)),
    }


def section_text(line_pool: list[str], *, line_target: int) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()
    for line in line_pool:
        stripped = line.strip()
        if stripped and stripped not in seen:
            seen.add(stripped)
            output.append(stripped)
        if len(output) >= line_target:
            break
    return output[:line_target]


def ordered_lines(line_pool: list[str], *, line_target: int) -> list[str]:
    output: list[str] = []
    for line in line_pool:
        stripped = line.strip()
        if stripped:
            output.append(stripped)
        if len(output) >= line_target:
            break
    return output[:line_target]


def rotate_lines(lines: list[str], rng: random.Random) -> list[str]:
    if len(lines) <= 1:
        return list(lines)
    start = rng.randrange(len(lines))
    return list(lines[start:] + lines[:start])


def rotate_lines_with_anchor(
    lines: list[str],
    *,
    anchor: str,
    rng: random.Random,
    anchor_position: int = 0,
) -> list[str]:
    ordered = [str(line).strip() for line in lines if str(line).strip()]
    if len(ordered) <= 1:
        return ordered
    if anchor and anchor in ordered:
        remaining = ordered[:]
        remaining.remove(anchor)
        rotated = rotate_lines(remaining, rng)
        insert_at = max(0, min(anchor_position, len(rotated)))
        return [*rotated[:insert_at], anchor, *rotated[insert_at:]]
    return rotate_lines(ordered, rng)


def limit_line_occurrences(lines: list[str], *, needle: str, max_occurrences: int) -> list[str]:
    if not needle or max_occurrences < 1:
        return [str(line).strip() for line in lines if str(line).strip()]
    count = 0
    limited: list[str] = []
    for line in lines:
        cleaned = str(line).strip()
        if not cleaned:
            continue
        if cleaned == needle:
            count += 1
            if count > max_occurrences:
                continue
        limited.append(cleaned)
    return limited


def limit_hook_leading_lines(lines: list[str], *, hook: str, max_occurrences: int) -> list[str]:
    normalized_hook = str(hook).strip()
    if not normalized_hook or max_occurrences < 1:
        return [str(line).strip() for line in lines if str(line).strip()]
    count = 0
    limited: list[str] = []
    for line in lines:
        cleaned = str(line).strip()
        if not cleaned:
            continue
        if cleaned.startswith(normalized_hook):
            count += 1
            if count > max_occurrences:
                continue
        limited.append(cleaned)
    return limited


def first_motif(card: dict[str, Any], fallback: str) -> str:
    motifs = [motif for motif in card.get("required_motifs", []) if motif]
    return motifs[0] if motifs else fallback


def second_motif(card: dict[str, Any], fallback: str) -> str:
    motifs = [motif for motif in card.get("required_motifs", []) if motif]
    return motifs[1] if len(motifs) > 1 else (motifs[0] if motifs else fallback)


def lyric_pronouns_for_plan(plan: dict[str, Any]) -> tuple[str, str]:
    mode = str(plan.get("primary_mode", "")).strip()
    seed = int(hashlib.md5(f"{plan['track_id']}:{mode}:pronouns".encode("utf-8")).hexdigest()[:8], 16)
    rng = random.Random(seed)
    if mode == "night_drive":
        speaker = rng.choice(["僕", "私"])
        listener = rng.choice(["君", "きみ"])
    elif mode == "anthemic_cinematic":
        speaker = rng.choice(["僕", "私"])
        listener = rng.choice(["君", "あなた"])
    else:
        speaker = rng.choice(["僕", "私", "あたし"])
        listener = rng.choice(["君", "あなた"])
    return speaker, listener


def conditioned_card_atoms(plan: dict[str, Any], card: dict[str, Any]) -> list[str]:
    context = plan.get("conditioning_context", {})
    atoms = unique_preserve_order(
        list(card.get("source_atoms", []))
        + list(card.get("conditioning_atoms", []))
        + list(card.get("required_motifs", []))
        + list(context.get("hook_atoms", []))
        + list(context.get("title_atoms", []))
    )
    strong_atoms = [
        item
        for item in atoms
        if is_safe_lyric_term(item)
        and item not in GENERIC_HOOK_ATOMS
        and item not in LOW_SIGNAL_CONDITIONING_ATOMS
        and "どうし" not in item
        and "以上意味" not in item
    ]
    if strong_atoms:
        return strong_atoms
    return [item for item in atoms if is_safe_lyric_term(item) and item not in GENERIC_HOOK_ATOMS]


def stable_atom_choice(atoms: list[str], fallback: str) -> str:
    for atom in atoms:
        if not atom.endswith(("て", "る", "い", "し")):
            return atom
    return atoms[0] if atoms else fallback


def source_line_contains(card: dict[str, Any], fragment: str) -> bool:
    return any(fragment in str(line) for line in card.get("source_lines", []))


def conditioned_pulse_word(raw_atoms: list[str], contrast_terms: list[str], hook_atoms: list[str]) -> str:
    for item in list(raw_atoms) + list(contrast_terms) + list(hook_atoms):
        if item in {"脈", "鼓動", "心拍"}:
            return item
        if "脈" in item:
            return "脈"
        if "鼓動" in item:
            return "鼓動"
        if "心拍" in item:
            return "心拍"
    return "脈"


def pick_variant(rng: random.Random, *options: str) -> str:
    choices = [option for option in options if str(option).strip()]
    return rng.choice(choices) if choices else ""


def conditioned_source_variants(
    card: dict[str, Any],
    *,
    section_name: str,
    speaker: str,
    listener: str,
    hook_atom: str,
    contrast_a: str,
    contrast_b: str,
    pulse_word: str,
    rng: random.Random,
) -> list[str]:
    variants: list[str] = []
    for source_line in card.get("source_lines", []):
        line = str(source_line or "").strip()
        if not line:
            continue
        if "聞き分け" in line:
            variants.extend(
                [
                    f"{listener}が{hook_atom}を飲み込む気配だけ やけに近く聞こえるのに",
                    f"{listener}の{hook_atom}だけ いやに近く聞こえるのに",
                ]
            )
            continue
        if ("だってない" in line or "ひとつない" in line) and section_name.startswith("verse"):
            variants.extend(
                [
                    f"{hook_atom}の狂いひとつない そう言い切ったのに",
                    f"{contrast_b}の狂いひとつない そう思い込んだのに",
                ]
            )
            continue
        if "記録" in line and "ジグザグ" in line:
            variants.extend(
                [
                    f"{contrast_a}に揃えたはずの線より {contrast_b}の方がまだ露骨だ",
                    f"{contrast_a}に記した跡より {contrast_b}の方がまだ生々しい",
                ]
            )
            continue
        if "それ以上意味" in line:
            variants.extend(
                [
                    f"{hook_atom}を これ以上きれいに説明しないで",
                    f"{hook_atom}に それ以上まともな意味をつけないで",
                ]
            )
            continue
        if "故にどんな顔して笑おうと" in line:
            variants.extend(
                [
                    f"故にどんな顔して笑おうと {contrast_b}だけは隠れない",
                    f"だからどんな顔で黙ろうと {contrast_b}だけは引き下がらない",
                ]
            )
            continue
        if "どうしたらいい" in line:
            heads = question_heads_from_lines([line])
            head = heads[0] if heads else hook_atom
            variants.extend(
                [
                    f"{head}はどうしたらいい?",
                    f"{head}はどこへ捨てればいい?",
                    f"{head}は誰に預ければいい?",
                ]
            )
            continue
        if "吐いては" in line and "脈" in line:
            variants.extend(
                [
                    f"証明しようのない {contrast_b}が {hook_atom}を吐いてまた{pulse_word}を打つ",
                    f"証明にならない {contrast_b}が {hook_atom}を吐いては{pulse_word}になる",
                ]
            )
            continue

    deduped = unique_preserve_order(variants)
    if section_name in {"chorus", "chorus_final"}:
        rng.shuffle(deduped)
    return deduped


def distinct_question_lines(head_a: str, head_b: str, rng: random.Random) -> list[str]:
    first = pick_variant(
        rng,
        f"{head_a}はどうしたらいい?",
        f"{head_a}はどこへ捨てればいい?",
    )
    second = pick_variant(
        rng,
        f"{head_b}は何で決めればいい?",
        f"{head_b}は誰に預ければいい?",
    )
    if second == first:
        second = f"{head_b}は誰に預ければいい?"
    return [first, second]


def conditioned_pulse_line(
    *,
    card: dict[str, Any],
    hook_atom: str,
    contrast_b: str,
    pulse_word: str,
    rng: random.Random,
) -> str:
    source_lines = [str(line).strip() for line in card.get("source_lines", []) if str(line or "").strip()]
    pulse = "脈" if any("脈" in line for line in source_lines) else pulse_word
    if any("証明" in line for line in source_lines) and any(("脈" in line) or ("エラー" in line) for line in source_lines):
        return pick_variant(
            rng,
            f"証明しようのない {contrast_b}が {hook_atom}を吐いてまた{pulse}を打つ",
            f"証明にならない {contrast_b}が エラーみたいに{pulse}を打ち返す",
            f"証明できない {contrast_b}が {hook_atom}を吐いては{pulse}になる",
        )
    return pick_variant(
        rng,
        f"証明しようのない{contrast_b}が {hook_atom}を吐いてまた{pulse}を打つ",
        f"証明にならない{contrast_b}が {hook_atom}を吐いては{pulse}になる",
    )


def night_drive_profile(card: dict[str, Any]) -> str:
    source_lines = [str(line or "").strip() for line in card.get("source_lines", []) if str(line or "").strip()]
    source_text = " ".join(source_lines)
    motifs = " ".join(str(item) for item in card.get("required_motifs", []) if str(item).strip())

    if any(fragment in source_text for fragment in ["優等生", "健康", "凡庸", "酒が空いた"]):
        return "usseewa"
    if any(fragment in source_text for fragment in ["踊りだせ", "孤独は殺菌", "おシェア", "ロンリー"]):
        return "odo"
    if any(fragment in source_text for fragment in ["正直言って", "左手", "ギラギラ", "夜を呑み"]):
        return "giragira"
    if any(fragment in source_text for fragment in ["Ready for my show", "唱タイム"]) or any(
        fragment in motifs for fragment in ["蛇腹刃", "蛇火", "タイム"]
    ):
        return "show"
    return ""


def render_night_drive_conditioned_section(
    *,
    plan: dict[str, Any],
    card: dict[str, Any],
    canonical: str,
    speaker: str,
    listener: str,
    hook: str,
    hook_atom: str,
    contrast_a: str,
    contrast_b: str,
    pulse_word: str,
    release_image: str,
    conditioned_decision: str,
    conditioned_release: str,
    rng: random.Random,
) -> list[str] | None:
    profile = night_drive_profile(card)
    line_target = card["line_target"]

    if not profile:
        return None
    section_bank = night_drive_profile_section_bank(profile, hook)
    selected_lines = section_bank.get(canonical)
    if not selected_lines:
        return None
    return ordered_lines(selected_lines, line_target=line_target)


def render_anthemic_conditioned_section(
    *,
    plan: dict[str, Any],
    card: dict[str, Any],
    section_name: str,
    canonical: str,
    speaker: str,
    listener: str,
    hook: str,
    hook_atom: str,
    contrast_a: str,
    contrast_b: str,
    pulse_word: str,
    release_image: str,
    conditioned_decision: str,
    conditioned_release: str,
    rng: random.Random,
) -> list[str] | None:
    profile = detect_anthemic_profile(card)
    line_target = card["line_target"]

    if not profile:
        return None
    section_bank = anthemic_profile_section_bank(profile, hook)
    selected_lines = section_bank.get(section_name) or section_bank.get(canonical)
    if not selected_lines:
        return None
    return ordered_lines(selected_lines, line_target=line_target)


def direct_emotional_focus_terms(
    profile: str,
    plan: dict[str, Any],
    card: dict[str, Any],
    hook: str,
) -> tuple[str, str, str, list[str]]:
    context = plan.get("conditioning_context", {})
    raw_motifs = [
        item
        for item in unique_preserve_order(
            list(card.get("required_motifs", []))
            + list(card.get("conditioning_atoms", []))
            + list(context.get("hook_atoms", []))
            + list(context.get("title_atoms", []))
        )
        if is_safe_lyric_term(item)
    ]
    motifs = [
        item
        for item in compact_direct_emotional_motifs(profile, raw_motifs)
        if is_safe_lyric_term(item)
    ]
    hook_lines = [
        str(item).strip()
        for item in context.get("hook_lines", [])
        if str(item).strip()
    ]
    preferred_keywords = direct_emotional_preferred_keywords(profile)
    preferred_matches: list[str] = []
    for keyword in preferred_keywords:
        match = best_direct_emotional_keyword_match(motifs, keyword)
        if match and match not in preferred_matches:
            preferred_matches.append(match)
    short_motifs = [
        item
        for item in motifs
        if len(str(item).strip()) <= 8
        and " " not in str(item)
        and "「" not in str(item)
        and "」" not in str(item)
        and "“" not in str(item)
        and "”" not in str(item)
        and "=" not in str(item)
    ]
    focus_pool = unique_preserve_order(preferred_matches + short_motifs + motifs)
    primary = focus_pool[0] if focus_pool else hook
    secondary = next((item for item in focus_pool if item != primary), primary)
    tertiary = next((item for item in focus_pool if item not in {primary, secondary}), secondary)
    return primary, secondary, tertiary, compact_direct_emotional_hook_lines(profile, hook, hook_lines)


def direct_emotional_source_variants(
    *,
    profile: str,
    plan: dict[str, Any],
    card: dict[str, Any],
    section_name: str,
    hook: str,
) -> list[str]:
    primary, secondary, tertiary, hook_lines = direct_emotional_focus_terms(profile, plan, card, hook)
    source_lines = [str(line).strip() for line in card.get("source_lines", []) if str(line or "").strip()]
    return build_direct_emotional_source_variants(
        profile=profile,
        section_name=section_name,
        hook=hook,
        primary=primary,
        secondary=secondary,
        tertiary=tertiary,
        hook_lines=hook_lines,
        source_lines=source_lines,
    )


def render_direct_emotional_conditioned_section(
    *,
    plan: dict[str, Any],
    card: dict[str, Any],
    section_name: str,
    canonical: str,
    hook: str,
    rng: random.Random,
) -> list[str] | None:
    track_id = str(plan.get("conditioning_context", {}).get("track_id", "")).strip()
    profile = detect_direct_emotional_profile(card, track_id=track_id)
    if not profile:
        return None
    section_bank = direct_emotional_profile_section_bank(profile, hook, track_id=track_id)
    static_lines = section_bank.get(section_name) or section_bank.get(canonical) or []
    dynamic_lines = direct_emotional_source_variants(
        profile=profile,
        plan=plan,
        card=card,
        section_name=section_name,
        hook=hook,
    )
    motif_primary = first_motif(card, hook)
    motif_secondary = second_motif(card, motif_primary)
    if profile == "gratitude_formula" and section_name == "verse_1":
        dynamic_lines = unique_preserve_order(
            dynamic_lines
            + [
                f"{motif_primary}を言いかけるたび ポケットの中で指先だけ熱を持つ",
                f"{motif_secondary}のあとで 机の端に触れた手まで少しやわらかくなる",
            ]
        )
    if profile == "gratitude_formula" and section_name == "verse_2":
        dynamic_lines = unique_preserve_order(
            dynamic_lines
            + [
                f"{motif_primary}を隠したままでも 胸ポケットの紙切れだけが体温を覚えている",
                f"{motif_secondary}のたびに 何気ない声までちゃんと今日の色になる",
            ]
        )
    if profile == "gratitude_formula" and section_name in {"bridge", "outro"}:
        dynamic_lines = unique_preserve_order(
            dynamic_lines
            + [
                f"{hook}のたびに しまい込んだ手紙の折り目までやわらかくなる",
                f"{motif_primary}のあとで 残ったぬくもりだけはまだ消えない",
            ]
        )
    if profile == "hopeful_runner" and section_name == "chorus_final":
        dynamic_lines = unique_preserve_order(
            dynamic_lines
            + [
                f"{hook} それでも足音だけは明日の方へ続いていく",
                f"{hook} それでも足音だけは明日の方へ続いていく",
                f"{motif_primary}を抱えたまま 朝焼けの方へ走っていく",
            ]
        )
    if profile == "hopeful_runner" and section_name == "outro":
        dynamic_lines = unique_preserve_order(
            dynamic_lines + [f"{hook}のあとも 足音だけはまだ消えない"]
        )
    if profile == "breakup_fixation" and section_name in {"bridge", "outro"}:
        dynamic_lines = unique_preserve_order(
            dynamic_lines
            + [
                f"{motif_primary}のあとに残った温度が 部屋を離れない",
                f"{motif_secondary}より早く 眠れない夜ばかり増えていく",
            ]
        )
    if profile == "gratitude_formula" and section_name in {"verse_1", "verse_2", "bridge", "outro"}:
        selected_lines = unique_preserve_order(dynamic_lines + static_lines)
    elif profile == "breakup_fixation" and section_name in {"verse_1", "verse_2", "bridge", "chorus_final", "outro"}:
        selected_lines = unique_preserve_order(dynamic_lines + static_lines)
    elif profile in {"gratitude_formula", "hopeful_runner"}:
        selected_lines = unique_preserve_order(static_lines + dynamic_lines)
    else:
        selected_lines = unique_preserve_order(dynamic_lines + static_lines)
    if not selected_lines:
        return None
    if section_name in {"chorus", "chorus_final"}:
        anchor_position = 0
        if section_name == "chorus_final" and profile in {"gratitude_formula", "breakup_fixation"}:
            # Let final chorus open on a release/detail line before the hook to reduce template openings.
            anchor_position = 1
        selected_lines = rotate_lines_with_anchor(
            selected_lines,
            anchor=hook,
            rng=rng,
            anchor_position=anchor_position,
        )
        if track_id == "deco27_animal":
            selected_lines = limit_line_occurrences(selected_lines, needle=hook, max_occurrences=1)
            selected_lines = limit_hook_leading_lines(selected_lines, hook=hook, max_occurrences=2)
    else:
        selected_lines = rotate_lines(selected_lines, rng)
    if track_id == "deco27_animal":
        ordered = section_text(selected_lines, line_target=card["line_target"])
    else:
        ordered = ordered_lines(selected_lines, line_target=card["line_target"])
    pruned = prune_direct_emotional_duplicates(ordered, selected_lines, line_target=card["line_target"])
    if track_id == "deco27_animal" and section_name in {"chorus", "chorus_final"}:
        pruned = section_text(limit_hook_leading_lines(pruned, hook=hook, max_occurrences=2), line_target=card["line_target"])
    return pruned


def render_intimate_conditioned_section(
    *,
    card: dict[str, Any],
    section_name: str,
    canonical: str,
    hook: str,
) -> list[str] | None:
    profile = detect_intimate_profile(card)
    if not profile:
        return None
    section_bank = intimate_profile_section_bank(profile, hook)
    selected_lines = section_bank.get(section_name) or section_bank.get(canonical)
    if not selected_lines:
        return None
    return ordered_lines(selected_lines, line_target=card["line_target"])


def render_dark_cute_conditioned_section(
    *,
    plan: dict[str, Any],
    card: dict[str, Any],
    section_name: str,
    canonical: str,
    speaker: str,
    listener: str,
    hook: str,
    hook_atom: str,
    contrast_a: str,
    contrast_b: str,
    conditioned_decision: str,
    conditioned_release: str,
    rng: random.Random,
) -> list[str] | None:
    if str(plan.get("primary_mode", "")).strip() != "dark_cute_breakdown":
        return None

    title_seed = str(plan.get("title_seed", "")).strip()
    sweet = hook_atom or contrast_a
    toxic = contrast_b if contrast_b and contrast_b != sweet else "毒"
    crack = next(
        (
            item
            for item in card.get("conditioning_atoms", [])
            if item and item not in {sweet, toxic} and is_safe_lyric_term(item)
        ),
        "ひび"
    )
    cute_word = default_cute_word(title_seed)

    source_variants = conditioned_source_variants(
        card,
        section_name=section_name,
        speaker=speaker,
        listener=listener,
        hook_atom=hook_atom,
        contrast_a=contrast_a,
        contrast_b=contrast_b,
        pulse_word="脈",
        rng=rng,
    )
    raw_atoms = [
        atom
        for atom in card.get("conditioning_atoms", [])
        if atom and atom not in {title_seed, sweet, toxic, crack} and is_safe_lyric_term(atom)
    ]
    mask_word = raw_atoms[0] if raw_atoms else "仮面"
    aftertaste_word = raw_atoms[1] if len(raw_atoms) > 1 else "残り香"

    bank = build_dark_cute_section_bank(
        title_seed=title_seed,
        sweet=sweet,
        toxic=toxic,
        crack=crack,
        cute_word=cute_word,
        mask_word=mask_word,
        aftertaste_word=aftertaste_word,
        hook=hook,
        conditioned_decision=conditioned_decision,
        conditioned_release=conditioned_release,
        source_variants=source_variants,
    )
    selected_lines = bank.get(section_name) or bank.get(canonical)
    if not selected_lines:
        return None
    if section_name in {"chorus", "chorus_final"}:
        selected_lines = rotate_lines_with_anchor(selected_lines, anchor=hook, rng=rng)
    else:
        selected_lines = rotate_lines(selected_lines, rng)
    return ordered_lines(selected_lines, line_target=card["line_target"])


def conditioned_final_decision_variants(conditioned_decision: str) -> list[str]:
    base = str(conditioned_decision or "").strip()
    if not base:
        return ["ここから誤魔化さない"]

    variants = [base]
    if base.startswith("ここから"):
        tail = base[len("ここから"):].strip()
        if tail:
            variants.extend(
                [
                    f"ここから先を{tail}",
                    f"ここから先は{tail}",
                    f"もう{tail}",
                ]
            )
    elif base.startswith("それでも"):
        tail = base[len("それでも"):].strip()
        if tail:
            variants.extend(
                [
                    f"ここから{tail}",
                    f"ここから先は{tail}",
                ]
            )
    return unique_preserve_order([item for item in variants if item])


def render_section_from_card(plan: dict[str, Any], card: dict[str, Any], rng: random.Random) -> list[str]:
    """
    Wrapper for section rendering that applies Phase 3 Phonetic Precision & Glitches.
    """
    lines = _render_section_from_card_raw(plan, card, rng)
    
    # 1. Apply Phonetic Precision & Glitch Automation (Phase 3)
    primary_mode = str(plan.get("primary_mode", "")).lower()
    glitch_intensity = plan.get("force_glitch_intensity", 0.0)
    glitch_style = "none"
    
    # Universal Glitch Logic
    if any(m in primary_mode for m in ["edm", "trance", "fast", "hyper", "glitch", "technical", "dark", "breakdown", "cut", "metal", "noise"]):
        glitch_style = "explosive"
        if glitch_intensity == 0:
            glitch_intensity = 0.2
    elif any(m in primary_mode for m in ["dream", "future", "digital", "liquid", "ambient"]):
        glitch_style = "melodic"
        if glitch_intensity == 0:
            glitch_intensity = 0.15
        
    if glitch_style != "none" and glitch_intensity > 0:
        final_lines = []
        for line in lines:
            # Only glitch non-empty lines, skip section headers
            if line and not (line.startswith("[") and line.endswith("]")):
                glitched = apply_stutter_glitch(line, style=glitch_style, intensity=glitch_intensity)
                final_lines.append(glitched)
            else:
                final_lines.append(line)
        lines = final_lines

    # 2. Suno v6 Phonetic Optimization
    lines = [optimize_for_suno_phonetics(line) for line in lines]
    
    return lines


def _render_section_from_card_raw(plan: dict[str, Any], card: dict[str, Any], rng: random.Random) -> list[str]:
    section_name = card["section"]
    canonical = card["canonical_section"]
    speaker, listener = lyric_pronouns_for_plan(plan)
    scene = card["scene"]
    motif_a = first_motif(card, "夜")
    motif_b = second_motif(card, motif_a)
    beats = plan["narrative_beats"]
    hook = plan["hook_blueprint"]["core_text"]
    bank = mode_jp_bank(str(plan.get("primary_mode", "")))
    pressure = rng.choice(bank["pressure_words"])
    decision = rng.choice(bank["decisions"])
    release_word = rng.choice(bank["release_words"])
    outro_word = rng.choice(bank["outro_words"])
    context = plan.get("conditioning_context", {})
    conditioned = bool(context.get("available"))
    raw_atoms = conditioned_card_atoms(plan, card)
    atom_a = stable_atom_choice(raw_atoms, motif_a)
    secondary_atoms = [item for item in raw_atoms if item != atom_a]
    atom_b = stable_atom_choice(secondary_atoms, motif_b)
    tertiary_atoms = [item for item in secondary_atoms if item != atom_b]
    atom_c = stable_atom_choice(tertiary_atoms, atom_a)
    hook_atoms = [item for item in context.get("hook_atoms", []) if is_safe_lyric_term(item)]
    hook_lines = [item for item in context.get("hook_lines", []) if is_safe_lyric_term(item)]
    contrast_terms = [item for item in context.get("contrast_terms", []) if is_safe_lyric_term(item)]
    fallback_hook_atom = next(
        (item for item in hook_atoms if item not in GENERIC_HOOK_ATOMS and item != hook),
        "",
    )
    hook_atom = fallback_hook_atom or atom_a
    contrast_a = contrast_terms[0] if contrast_terms else atom_a
    contrast_b = contrast_terms[1] if len(contrast_terms) > 1 else atom_b
    question_heads = unique_preserve_order(
        [item for item in card.get("question_heads", []) if str(item).strip()]
        + [item for item in context.get("hook_shape", {}).get("question_heads", []) if str(item).strip()]
    )
    if context.get("track_id") == "ado_readymade" and canonical not in {"chorus", "chorus_final"}:
        hook_atoms = [item for item in hook_atoms if item != "弾け飛んだ"]
        raw_atoms = [item for item in raw_atoms if item != "弾け飛んだ"]
        fallback_hook_atom = next(
            (item for item in hook_atoms if item not in GENERIC_HOOK_ATOMS and item != hook),
            fallback_hook_atom,
        )
        hook_atom = fallback_hook_atom or atom_a
    pulse_word = conditioned_pulse_word(raw_atoms, contrast_terms, hook_atoms)
    conditioned_release = rng.choice(CONDITIONED_RELEASE_BANK)
    conditioned_decision = rng.choice(CONDITIONED_DECISION_BANK)
    release_image = next(
        (
            item
            for item in card.get("required_motifs", [])
            if is_safe_lyric_term(str(item))
            and str(item) not in {hook_atom, contrast_a, contrast_b}
            and str(item) not in LOW_SIGNAL_CONDITIONING_ATOMS
        ),
        hook_atom,
    )
    source_variants = conditioned_source_variants(
        card,
        section_name=section_name,
        speaker=speaker,
        listener=listener,
        hook_atom=hook_atom,
        contrast_a=contrast_a,
        contrast_b=contrast_b,
        pulse_word=pulse_word,
        rng=rng,
    )
    anthemic_specific = render_anthemic_conditioned_section(
        plan=plan,
        card=card,
        section_name=section_name,
        canonical=canonical,
        speaker=speaker,
        listener=listener,
        hook=hook,
        hook_atom=hook_atom,
        contrast_a=contrast_a,
        contrast_b=contrast_b,
        pulse_word=pulse_word,
        release_image=release_image,
        conditioned_decision=conditioned_decision,
        conditioned_release=conditioned_release,
        rng=rng,
    )
    if anthemic_specific is not None:
        return anthemic_specific
    night_drive_specific = render_night_drive_conditioned_section(
        plan=plan,
        card=card,
        canonical=canonical,
        speaker=speaker,
        listener=listener,
        hook=hook,
        hook_atom=hook_atom,
        contrast_a=contrast_a,
        contrast_b=contrast_b,
        pulse_word=pulse_word,
        release_image=release_image,
        conditioned_decision=conditioned_decision,
        conditioned_release=conditioned_release,
        rng=rng,
    )
    if night_drive_specific is not None:
        return night_drive_specific
    dark_cute_specific = render_dark_cute_conditioned_section(
        plan=plan,
        card=card,
        section_name=section_name,
        canonical=canonical,
        speaker=speaker,
        listener=listener,
        hook=hook,
        hook_atom=hook_atom,
        contrast_a=contrast_a,
        contrast_b=contrast_b,
        conditioned_decision=conditioned_decision,
        conditioned_release=conditioned_release,
        rng=rng,
    )
    if dark_cute_specific is not None:
        return dark_cute_specific
    if str(plan.get("primary_mode", "")).strip() == "direct_emotional_pop":
        direct_specific = render_direct_emotional_conditioned_section(
            plan=plan,
            card=card,
            section_name=section_name,
            canonical=canonical,
            hook=hook,
            rng=rng,
        )
        if direct_specific is not None:
            return direct_specific
    intimate_specific = render_intimate_conditioned_section(
        card=card,
        section_name=section_name,
        canonical=canonical,
        hook=hook,
    )
    if intimate_specific is not None:
        return intimate_specific
    if str(plan.get("primary_mode", "")).strip() == "anthemic_cinematic" and conditioned and canonical == "chorus":
        anthem_hook = next(
            (item for item in hook_lines if len(str(item).strip()) <= 12),
            next((item for item in hook_atoms if item not in GENERIC_HOOK_ATOMS), hook),
        )
        if section_name == "chorus_open":
            return ordered_lines(
                [
                    pick_variant(
                        rng,
                        f"{anthem_hook} ここから開け",
                        f"{anthem_hook} まだ高く",
                        f"{anthem_hook} いま火花を上げる",
                    ),
                    f"{conditioned_release} {hook_atom}まで黙らせない",
                    f"{contrast_a}じゃ裁けない {contrast_b}がまだ疼く",
                    f"{conditioned_decision}",
                ],
                line_target=card["line_target"],
            )
        if section_name == "chorus_2":
            return ordered_lines(
                [
                    pick_variant(
                        rng,
                        f"{anthem_hook} もっと遠くへ",
                        f"{anthem_hook} まだ広がる",
                        f"{anthem_hook} ここで燃え上がる",
                    ),
                    f"{conditioned_release} {hook_atom}まで黙らせない",
                    f"{contrast_a}じゃ裁けない {contrast_b}がまだ疼く",
                    f"{conditioned_decision}",
                    f"{anthem_hook}",
                ],
                line_target=card["line_target"],
            )
        if section_name == "chorus":
            return ordered_lines(
                [
                    f"{anthem_hook}",
                    f"{conditioned_release} {hook_atom}まで黙らせない",
                    f"{contrast_a}じゃ裁けない {contrast_b}がまだ疼く",
                    f"{conditioned_decision}",
                ],
                line_target=card["line_target"],
            )
        if section_name == "chorus_final":
            return ordered_lines(
                [
                    f"{anthem_hook}",
                    f"{conditioned_release} {hook_atom}も{contrast_b}も抱えていく",
                    f"{contrast_a}じゃ切れない {contrast_b}をこの喉で引き受ける",
                    f"{hook_atom}の誤差ごと 最後まで飲み込まない",
                    f"ここから {conditioned_decision}",
                ],
                line_target=card["line_target"],
            )
    if canonical == "intro" and conditioned:
        if source_line_contains(card, "聞き分け"):
            return ordered_lines(
                [
                    pick_variant(
                        rng,
                        f"{listener}の{atom_a}だけ いやに近く聞こえるのに",
                        f"{listener}が{atom_a}を飲み込む気配だけ やけに近く聞こえるのに",
                    ),
                    pick_variant(
                        rng,
                        f"{hook_atom}の方が {speaker}より先にこちらを見抜いてくる",
                        f"{hook_atom}の方が {speaker}より先にこちらを見抜いてくる",
                    ),
                    pick_variant(
                        rng,
                        f"{pulse_word}ひとつで 平熱の方がずれていく",
                        f"{pulse_word}ひとつで まともな顔の方が先に崩れていく",
                    ),
                ],
                line_target=card["line_target"],
            )
        return section_text(
            [
                f"{atom_a}ひとつで {speaker}の平熱がずれる",
                f"{hook_atom}だけが {speaker}より先にこちらを見抜いてくる",
                f"{pressure}を飲み込んでも {hook_atom}の気配は消えない",
            ],
            line_target=card["line_target"],
        )

    if canonical == "intro":
        return section_text(
            [
                f"{scene}で {motif_a}だけが先にうるさかった",
                f"{pressure}を隠したまま {speaker}はまだ目をそらせない",
            ],
            line_target=card["line_target"],
        )

    if canonical == "verse_1" and conditioned:
        if source_line_contains(card, "だってない") or source_line_contains(card, "記録"):
            return ordered_lines(
                [
                    pick_variant(
                        rng,
                        f"{atom_a}の狂いひとつない そう言い切ったのに",
                        f"{atom_a}まで狂ってない そう思い込んだのに",
                        f"狂いひとつないはずだと 先に言い聞かせたのに",
                        "異常なしだと言い切る声から 先に濁っていた",
                    ),
                    pick_variant(
                        rng,
                        f"{contrast_a}に記した跡より {contrast_b}の方がむしろ生々しい",
                        f"{contrast_a}に揃えたはずの線より {contrast_b}の方が先に露骨だ",
                        f"{contrast_a}の線より {contrast_b}の方がよほど正直だ",
                        f"記録の線より {contrast_b}の方が先に本性を出す",
                    ),
                    pick_variant(
                        rng,
                        f"{hook_atom}に それ以上まともな意味をつけないで",
                        f"{hook_atom}を これ以上きれいに説明しないで",
                        f"{hook_atom}を まともな名前で片づけないで",
                        f"{hook_atom}に これ以上お利口な説明を与えないで",
                    ),
                    pick_variant(
                        rng,
                        f"故にどんな顔して笑おうと {contrast_b}だけは隠れない",
                        f"故にどんな顔して笑おうと {contrast_b}まで隠れない",
                        f"平気な顔のままでも {contrast_b}だけ喉に残る",
                        f"笑ったふりほど {contrast_b}の輪郭だけが顔に残る",
                        f"笑顔を貼るほど {contrast_b}だけが喉に残る",
                    ),
                ],
                line_target=card["line_target"],
            )
        pool = [
            f"{atom_a}ひとつで 平気な顔がずれていく",
            f"{atom_b}まで綺麗に並べても {speaker}の中はまだ測れない",
            f"{scene}で {speaker}は{contrast_a}より鈍い{contrast_b}を庇っていた",
            f"{listener}に向ける前に {hook_atom}が喉の奥で引っかかる",
            beats["opening_state"],
        ]
        rng.shuffle(pool)
        return section_text(pool, line_target=card["line_target"])

    if canonical == "verse_1":
        pool = [
            f"{scene}で、{speaker}は言い切れない本音を噛み殺したまま朝をやり過ごした",
            f"{motif_a}みたいな沈黙が {motif_b}の輪郭だけを濃くしていく",
            beats["opening_state"],
            f"{listener}に届かない言葉ほど {motif_a}みたいに身体の奥へ沈んでいく",
            f"{motif_b}の気配まで抱えたまま まだ平気なふりをしていた",
        ]
        rng.shuffle(pool)
        return section_text(pool, line_target=card["line_target"])

    if section_name == "pre_chorus_2" and conditioned:
        if source_line_contains(card, "だってない") or source_line_contains(card, "記録"):
            return ordered_lines(
                [
                    pick_variant(
                        rng,
                        f"{contrast_a}のふりをした {contrast_b}が喉で暴れる",
                        f"{contrast_a}みたいな顔した {contrast_b}が喉の奥で暴れる",
                    ),
                    pick_variant(
                        rng,
                        f"{hook_atom}の名を飲み込むたび {pulse_word}だけがうるさくなる",
                        f"{hook_atom}の名を飲み込むたび {pulse_word}ばかりうるさくなる",
                        f"{hook_atom}を噛み殺すたび {pulse_word}だけが遅れて騒ぎ出す",
                    ),
                    pick_variant(
                        rng,
                        f"だからもう {hook_atom}をなかったことにできない",
                        f"だからもう {contrast_b}ごと切り捨てられない",
                    ),
                ],
                line_target=card["line_target"],
            )
        pool = [
            pick_variant(
                rng,
                f"{pressure}がもう整わない",
                f"噛みしめた声さえ もう綺麗に整わない",
            ),
            f"{TURN_MARKERS[rng.randrange(len(TURN_MARKERS))]}、今度は{hook_atom}ごと隠さない",
            f"{contrast_a}のふりをした {contrast_b}が喉で暴れる",
        ]
        return ordered_lines(pool, line_target=card["line_target"])

    if section_name == "pre_chorus_2":
        pool = [
            f"{pressure}がもう隠し切れない",
            f"{motif_a}の傷が閉じる前に {speaker}は次の一歩を選ぶ",
            f"{TURN_MARKERS[rng.randrange(len(TURN_MARKERS))]}、今度は逃がさない",
        ]
        rng.shuffle(pool)
        return section_text(pool, line_target=card["line_target"])

    if canonical == "pre_chorus" and conditioned:
        if source_line_contains(card, "だってない") or source_line_contains(card, "記録"):
            return ordered_lines(
                [
                    pick_variant(
                        rng,
                        f"{contrast_a}に寄せるほど {contrast_b}だけが濃くなる",
                        f"{contrast_a}に寄せるほど {contrast_b}ばかり濃くなる",
                        f"{contrast_a}に寄せるたび {contrast_b}の輪郭ばかり濃くなる",
                        f"きちんと寄せるほど {contrast_b}だけが濃くなる",
                    ),
                    pick_variant(
                        rng,
                        f"{hook_atom}の名を飲み込むたび {pulse_word}だけが遅れて暴れる",
                        f"{hook_atom}の名を飲み込むたび {pulse_word}ばかり遅れて暴れる",
                        f"{hook_atom}の名を噛むたび {pulse_word}の方が遅れて暴れる",
                        f"{hook_atom}を飲み込むほど {pulse_word}が遅れて暴れ出す",
                    ),
                    pick_variant(
                        rng,
                        f"だから {contrast_a}じゃ追いつかない",
                        f"だから 診断じゃ追いつかない",
                    ),
                ],
                line_target=card["line_target"],
            )
        pool = [
            f"{atom_a}を飲み込むたび {atom_b}だけが濃くなる",
            f"{TURN_MARKERS[rng.randrange(len(TURN_MARKERS))]}、{contrast_a}じゃ追いつかない",
            f"{hook_atom}の手前で {speaker}の鼓動だけが先に暴れる",
        ]
        rng.shuffle(pool)
        return section_text(pool, line_target=card["line_target"])

    if canonical == "pre_chorus":
        pool = [
            f"{beats['pressure_point']}",
            f"{motif_a}の輪郭を噛みしめるたび 夜の密度だけが変わっていく",
            f"{TURN_MARKERS[rng.randrange(len(TURN_MARKERS))]}、{speaker}の鼓動だけが先に尖っていく",
        ]
        rng.shuffle(pool)
        return section_text(pool, line_target=card["line_target"])

    if canonical == "chorus" and conditioned:
        if question_heads:
            head_a = question_heads[0]
            head_b = question_heads[1] if len(question_heads) > 1 else f"{contrast_a}の境目"
            pulse_line = conditioned_pulse_line(
                card=card,
                hook_atom=hook_atom,
                contrast_b=contrast_b,
                pulse_word=pulse_word,
                rng=rng,
            )
            q1, q2 = distinct_question_lines(head_a, head_b, rng)
            pool = [
                hook,
                q1,
                q2,
                pulse_line,
                f"{hook}",
            ]
            return ordered_lines(pool, line_target=card["line_target"])
        pool = [
            hook,
            f"{conditioned_release} {atom_a}まで黙らせない",
            f"{contrast_a}じゃ裁けない {contrast_b}がまだ疼く",
            f"{conditioned_decision}",
            f"{hook}",
        ]
        return ordered_lines(pool, line_target=card["line_target"])

    if canonical == "chorus":
        pool = [
            hook,
            f"{release_word} {motif_b}だけは嘘じゃない",
            f"{motif_a}の先で {speaker}はまだ消えない方を選ぶ",
            f"{decision}",
            f"{hook}",
        ]
        return ordered_lines(pool, line_target=card["line_target"])

    if canonical == "verse_2" and conditioned:
        if source_line_contains(card, "だってない") or source_line_contains(card, "記録"):
            return ordered_lines(
                [
                    pick_variant(
                        rng,
                        f"{atom_a}まで正しい顔をして {speaker}の方が先にずれる",
                        f"{atom_a}まで正しいふりして {speaker}の方が先にずれる",
                        f"正しさの列に立つほど {speaker}の方が先にずれる",
                    ),
                    pick_variant(
                        rng,
                        f"{contrast_a}に揃えるほど {contrast_b}だけが綺麗に壊れていく",
                        f"{contrast_a}に揃えるほど {contrast_b}ばかり綺麗に壊れていく",
                        f"{contrast_a}に揃えるたび {contrast_b}の輪郭ばかり綺麗に壊れる",
                    ),
                    f"{listener}に触れた瞬間 {hook_atom}の誤差が{pulse_word}を打つ",
                    pick_variant(
                        rng,
                        f"故にどんな顔で黙ろうと {contrast_b}だけは引き下がらない",
                        f"故にどんな顔で黙ろうと {contrast_b}まで引き下がらない",
                        f"黙って平気を装っても {contrast_b}だけ先に喉へ上がる",
                        f"平気のふりを噛むほど {contrast_b}だけ先に喉へ上がる",
                    ),
                ],
                line_target=card["line_target"],
            )
        pool = [
            f"{scene}で {atom_a}だけが余計に正しく見えた",
            f"{atom_b}みたいな顔で誤魔化しても {speaker}の底は軋んでいく",
            f"{listener}に触れた瞬間 {hook_atom}の誤差が暴れ出す",
            f"{contrast_a}より先に {contrast_b}が本音を裂いていく",
            beats["turn_point"],
        ]
        rng.shuffle(pool)
        return section_text(pool, line_target=card["line_target"])

    if canonical == "verse_2":
        pool = [
            f"{scene}で、{motif_a}だけがまっすぐ鳴っていた",
            f"{motif_b}みたいに遅れてきた本音が {motif_a}に熱を持っていく",
            f"{TURN_MARKERS[rng.randrange(len(TURN_MARKERS))]}、{speaker}は平気な顔をやめていく",
            f"{listener}に言えなかった言葉ほど 未来の方へ急いでいく",
            beats["turn_point"],
        ]
        rng.shuffle(pool)
        return section_text(pool, line_target=card["line_target"])

    if section_name == "bridge_rise" and conditioned:
        if question_heads:
            pool = [
                pick_variant(
                    rng,
                    f"{conditioned_release} {hook_atom}を隠す方が無理だ",
                    f"{conditioned_release} {hook_atom}だけ引っ込めるなんて無理だ",
                ),
                pick_variant(
                    rng,
                    f"{contrast_a}じゃ切れない {contrast_b}ごと叫び返す",
                    f"{contrast_a}じゃ裁けない {contrast_b}ごと声に変える",
                ),
                f"{conditioned_decision}",
            ]
            return section_text(pool, line_target=card["line_target"])
        pool = [
            f"{conditioned_release} {conditioned_decision}",
            f"{atom_a}の誤差ごと ここでは飲み込まない",
            f"{pressure}より大きい声で {hook_atom}を呼び直す",
        ]
        rng.shuffle(pool)
        return section_text(pool, line_target=card["line_target"])

    if section_name == "bridge_rise":
        pool = [
            f"{release_word} {decision}",
            f"{motif_b}まで連れて ここから先へ踏み出す",
            f"{pressure}より大きい声で 明日を呼び直す",
        ]
        rng.shuffle(pool)
        return section_text(pool, line_target=card["line_target"])

    if canonical == "bridge" and conditioned:
        if question_heads:
            head = question_heads[0]
            return ordered_lines(
                [
                    f"{head}に答えなんて いまは持てない",
                    f"{contrast_a}より生々しい {contrast_b}を {speaker}は抱えたまま立っている",
                    f"{hook_atom}まで喉の奥で 噛み砕くしかない",
                ],
                line_target=card["line_target"],
            )
        pool = [
            beats["turn_point"],
            f"{contrast_a}より生々しい {contrast_b}を {speaker}は抱えたまま立っている",
            f"{scene}の端で {atom_a}まで味方に変えていく",
        ]
        rng.shuffle(pool)
        return section_text(pool, line_target=card["line_target"])

    if canonical == "bridge":
        pool = [
            beats["turn_point"],
            f"{motif_a}は飾りじゃなくて {speaker}の手のひらに残った証明だ",
            f"{scene}の端で やっと{speaker}は目を上げた",
        ]
        rng.shuffle(pool)
        return section_text(pool, line_target=card["line_target"])

    if canonical == "chorus_final" and conditioned:
        if question_heads:
            head = question_heads[0]
            final_release_line = pick_variant(
                rng,
                f"{conditioned_release} {hook_atom}も{contrast_b}も抱え込む",
                f"{conditioned_release} {hook_atom}も{contrast_b}も投げ捨てない",
            )
            final_carry_line = pick_variant(
                rng,
                f"{contrast_a}じゃ切れない {contrast_b}と{release_image}をこの喉で引き受ける",
                f"{contrast_a}じゃ切れない {contrast_b}と{release_image}をこの声で背負い直す",
            )
            final_decision_line = pick_variant(
                rng,
                *conditioned_final_decision_variants(conditioned_decision),
            )
            pool = [
                hook,
                f"{head}はまだ終わらない?",
                final_release_line,
                final_carry_line,
                final_decision_line,
                f"{hook}",
            ]
            return ordered_lines(pool, line_target=card["line_target"])
        pool = [
            hook,
            f"{conditioned_release} {atom_a}も{atom_b}も抱えていく",
            f"{contrast_a}じゃ切れない {contrast_b}をこの喉で引き受ける",
            f"{hook_atom}の誤差ごと 最後まで飲み込まない",
            f"ここから {conditioned_decision}",
            f"{hook}",
        ]
        return ordered_lines(pool, line_target=card["line_target"])

    if canonical == "chorus_final":
        pool = [
            hook,
            f"{release_word} {motif_b}ごと抱えていく",
            f"{speaker}は{motif_a}ごと 明日の方へ踏み出していく",
            beats["release_point"],
            f"{decision}",
            f"{hook}",
        ]
        return ordered_lines(pool, line_target=card["line_target"])

    if canonical == "outro" and conditioned:
        outro_scene = scene
        if (
            not is_safe_lyric_term(outro_scene)
            or len(outro_scene) < 3
            or outro_scene in LOW_SIGNAL_CONDITIONING_ATOMS
        ):
            outro_scene = "喉"
        pool = [
            pick_variant(
                rng,
                f"{outro_scene}の隅で {speaker}はようやく{hook_atom}の置き場を間違えない",
                f"{outro_scene}の隅で {speaker}はようやく{hook_atom}を見失わない",
                f"{outro_scene}の隅で {speaker}はようやく{hook_atom}を取り落とさない",
            ),
            pick_variant(
                rng,
                f"{outro_word}めいた {atom_c}が 次の朝まで残っていく",
                f"{outro_word}めいた {atom_c}ばかり 次の朝まで残っていく",
                f"{outro_word}めいた {hook_atom}が 朝の手前まで残っていく",
                f"{outro_word}めいた {atom_c}が 次の朝まで剥がれない",
            ),
        ]
        return section_text(pool, line_target=card["line_target"])

    if canonical == "outro":
        pool = [
            f"{scene}の隅で {speaker}はようやく{motif_a}を見つけた",
            f"{outro_word}みたいな余熱だけが 次の朝まで残っていく",
        ]
        return section_text(pool, line_target=card["line_target"])

    pool = [
        f"{scene}で {motif_a}が揺れていた",
        beats["opening_state"],
    ]
    return section_text(pool, line_target=card["line_target"])


def render_candidate(plan: dict[str, Any], *, variant_index: int) -> dict[str, Any]:
    rng = random.Random(int(hashlib.md5(f"{plan['track_id']}:{variant_index}".encode("utf-8")).hexdigest()[:8], 16))
    bank = mode_jp_bank(str(plan.get("primary_mode", "")))
    conditioning_titles = [
        item
        for item in plan.get("conditioning_context", {}).get("title_atoms", [])
        if is_safe_lyric_term(item) and item not in GENERIC_HOOK_ATOMS
    ]
    title_core = rng.choice(conditioning_titles or bank["title_roots"])
    if str(plan.get("primary_mode", "")).strip() == "direct_emotional_pop":
        title = title_core
    else:
        title_suffixes = unique_preserve_order(
            [
                *[
                    item
                    for item in plan.get("conditioning_context", {}).get("hook_atoms", [])[1:4]
                    if is_safe_lyric_term(item) and item != title_core
                ],
                "余熱",
                "輪郭",
                "残響",
                "行方",
            ]
        )
        title = f"{title_core}の{rng.choice(title_suffixes)}"

    lines = [
        f"# {title}",
        "",
    ]
    for card in plan["section_cards"]:
        lines.append(f"[{card['section']}]")
        lines.extend(render_section_from_card(plan, card, rng))
        lines.append("")

    markdown_text = "\n".join(lines).strip() + "\n"
    return {
        "candidate_id": f"{plan['track_id']}-candidate-{variant_index + 1}",
        "variant_index": variant_index + 1,
        "title": title,
        "markdown": markdown_text,
    }


def motif_coverage_score(plan: dict[str, Any], markdown_text: str) -> float:
    body = markdown_text
    required = [motif for item in plan["motif_roster"] for motif in item.get("motifs", [])[:2]]
    required = unique_preserve_order(required)
    if not required:
        return 0.0
    hits = sum(1 for motif in required if motif_matches_text(motif, body))
    return round(min(1.0, hits / max(4, len(required) * 0.6)), 2)


def motif_match_terms(motif: str) -> list[str]:
    cleaned = str(motif or "").strip()
    if not cleaned:
        return []
    terms = [cleaned]
    if "言葉はいらない" in cleaned and "キスをして" in cleaned:
        terms.extend(["言葉はいらない", "キス", "食らいつく", "噛みつく", "噛み砕いて"])
    elif "キスをして" in cleaned:
        terms.extend(["キス", "食らいつく", "噛みつく"])
    if "弾け飛んだ" in cleaned:
        terms.extend(["弾け飛んだ", "弾け", "飛んだ"])
    if "本音ばかり" in cleaned:
        terms.extend(["本音ばかり", "本音"])
    if "寄る" in cleaned:
        terms.extend(["寄る辺ない", "侘しさ"])
    if "新時代はこ" in cleaned:
        terms.extend(["新時代", "未来"])
    if cleaned.endswith("未来だ") or "この未来" in cleaned:
        terms.append("未来")
    if "世界中全部" in cleaned:
        terms.extend(["世界", "塗り替える"])
    if "変えてしま" in cleaned:
        terms.extend(["変える", "塗り替える"])
    if "果てしない音楽" in cleaned:
        terms.append("音楽")
    terms.extend(extract_japanese_lexical_atoms([cleaned], limit=4))
    return unique_preserve_order(term for term in terms if term and len(term) >= 2)


def motif_matches_text(motif: str, text: str) -> bool:
    return any(term in text for term in motif_match_terms(motif))


def plan_alignment_score(plan: dict[str, Any], markdown_text: str) -> float:
    section_lookup = {section: lines for section, lines in extract_section_blocks(markdown_text)}
    hits = 0
    possible = 0
    for card in plan["section_cards"]:
        section = card["section"]
        if section not in section_lookup:
            continue
        possible += 1
        body = " ".join(section_lookup[section])
        required_motifs = [motif for motif in card.get("required_motifs", [])[:2] if motif]
        if not required_motifs:
            hits += 1
            continue
        if any(motif_matches_text(motif, body) for motif in required_motifs):
            hits += 1
    return round(hits / max(1, possible), 2)


def hook_control_score(plan: dict[str, Any], markdown_text: str) -> float:
    lines = lyric_lines(markdown_text)
    if not lines:
        return 0.0
    counts = Counter(lines)
    max_repeat = max(counts.values())
    expected_high = plan.get("hook_density") == "high"
    conditioning_context = plan.get("conditioning_context", {})
    track_id = str(conditioning_context.get("track_id", "")).strip()
    title_ignition_style = str(conditioning_context.get("title_ignition_style", "")).strip()
    hook_copy_force = str(conditioning_context.get("hook_copy_force", "")).strip()
    primary_mode = str(plan.get("primary_mode", "")).strip()
    form_tags = {str(tag).strip() for tag in plan.get("form_profile", {}).get("tags", []) if str(tag).strip()}
    chant_tolerant_medium = track_id == "deco27_animal" or (
        primary_mode == "direct_emotional_pop"
        and title_ignition_style == "formulaic"
        and "title_object" in form_tags
    )
    ironic_title_chant = (
        primary_mode == "ironic_meta"
        and title_ignition_style in {"formulaic", "ironic"}
        and hook_copy_force == "heavy"
    )
    if expected_high:
        if ironic_title_chant:
            return 1.0 if 2 <= max_repeat <= 4 else 0.7 if max_repeat == 1 else 0.45
        return 1.0 if 2 <= max_repeat <= 3 else 0.7 if max_repeat == 1 else 0.45
    # Title-object chant tracks can legitimately reuse the same nucleus across chorus and final chorus
    # without losing hook control.
    # Ironic slogan tracks also repeat the title line as an intentional rally/deflation device.
    allowed_repeat = 4 if (chant_tolerant_medium or ironic_title_chant) else 2
    return 1.0 if max_repeat <= allowed_repeat else 0.6


def novelty_score(markdown_text: str) -> float:
    lines = lyric_lines(markdown_text)
    if not lines:
        return 0.0
    opening_counts = Counter(line[:4] for line in first_lines(markdown_text) if len(line) >= 4)
    repeated_openings = sum(max(0, count - 1) for count in opening_counts.values())
    repeated_lines = sum(max(0, count - 1) for count in Counter(lines).values())
    scaffold_markers = ["だけが", "だけは", "まま", "まだ", "みたい", "先で", "先を", "やっと"]
    scaffold_hits = sum(sum(line.count(marker) for marker in scaffold_markers) for line in lines)
    penalty = repeated_openings * 0.08 + repeated_lines * 0.04 + scaffold_hits * 0.02
    return round(max(0.0, 1.0 - penalty), 2)


def final_release_score(plan: dict[str, Any], markdown_text: str) -> float:
    sections = {section: lines for section, lines in extract_section_blocks(markdown_text)}
    chorus_lines = sections.get("chorus", [])
    final_lines = sections.get("chorus_final", [])
    chorus_text = " ".join(chorus_lines)
    final_text = " ".join(final_lines)
    if not final_text:
        return 0.0
    requirements = plan.get("final_release_requirements", {})
    primary_mode = str(plan.get("primary_mode", "")).strip()
    conditioning_context = plan.get("conditioning_context", {})
    title_ignition_style = str(conditioning_context.get("title_ignition_style", "")).strip()
    form_tags = {str(tag).strip() for tag in plan.get("form_profile", {}).get("tags", []) if str(tag).strip()}
    markers = requirements.get("release_markers") or ["明日", "未来", "ここから", "踏み出す", "連れていく", "次の"]
    new_images = [image for image in requirements.get("required_new_images", []) if image]
    decisive_phrases = [
        "離さない",
        "逸らさない",
        "信じる",
        "越えて",
        "変えて",
        "連れてくる",
        "連れていく",
        "ここから",
    ]

    score = 0.0
    if any(marker in final_text for marker in markers):
        score += 0.35
    if len(sections.get("chorus_final", [])) >= len(chorus_lines):
        score += 0.2
    if any(image in final_text and image not in chorus_text for image in new_images):
        score += 0.25
    if any(phrase in final_text for phrase in decisive_phrases):
        score += 0.2
    title_object_chant = (
        primary_mode == "direct_emotional_pop"
        and title_ignition_style == "formulaic"
        and "title_object" in form_tags
    )
    if title_object_chant:
        unique_final_lines = [line for line in final_lines if line and line not in chorus_lines]
        if any(marker in final_text for marker in {"ここから", "最後まで"}) and any(
            term in final_text for term in {"食らいつく", "噛みつく", "抱えていく"}
        ):
            score += 0.25
        elif len(unique_final_lines) >= 2 and any(marker in final_text for marker in {"ここから", "最後まで"}):
            score += 0.15
    if primary_mode == "ironic_meta":
        unique_final_lines = [line for line in final_lines if line and line not in chorus_lines]
        if len(unique_final_lines) >= 2:
            score += 0.15
        if any(image in final_text for image in new_images):
            score += 0.1
    return round(min(1.0, score), 2)


def specificity_score(plan: dict[str, Any], markdown_text: str) -> float:
    concrete_words = []
    for item in plan["motif_roster"]:
        concrete_words.extend(item.get("motifs", []))
        concrete_words.extend(item.get("scene_candidates", []))
    concrete_words = unique_preserve_order(concrete_words)
    abstract_markers = ["言葉", "弱さ", "本音", "未来", "輪郭", "気配", "証明", "夜", "明日"]
    concretized_phrases = [
        "乱れの輪郭",
        "輪郭ばかり",
        "記した跡",
        "喉の隅",
        "鼓動を打つ",
        "脈を打つ",
        "世界ごと塗り替える",
        "果てしない音楽",
        "未来の拍",
        "自由の輪郭",
    ]
    concrete_hits = sum(1 for word in concrete_words if word and word in markdown_text)
    concrete_hits += sum(markdown_text.count(phrase) * 0.7 for phrase in concretized_phrases)
    abstract_hits = sum(markdown_text.count(marker) for marker in abstract_markers)
    abstract_hits -= markdown_text.count("乱れの輪郭")
    abstract_hits -= markdown_text.count("輪郭ばかり")
    abstract_hits -= markdown_text.count("未来の拍")
    abstract_hits -= markdown_text.count("自由の輪郭")
    abstract_hits = max(0.0, float(abstract_hits))
    return round(concrete_hits / max(1, concrete_hits + abstract_hits * 0.7), 2)


def jp_hook_force_score(candidate_title: str, markdown_text: str) -> float:
    profile = build_markdown_japanese_profile(candidate_title, markdown_text)
    label = profile.get("hook_copy_force", "low")
    return {
        "low": 0.45,
        "medium": 0.72,
        "high": 1.0,
    }.get(str(label), 0.45)


def jp_section_flow_score(markdown_text: str, candidate_title: str) -> float:
    profile = build_markdown_japanese_profile(candidate_title, markdown_text)
    features = profile.get("section_features", [])
    if not features:
        return 0.0

    roles = [item.get("jp_section_role") for item in features]
    phrase_roles = [item.get("phrase_energy_role") for item in features]
    score = 0.0
    if "a_melo" in roles:
        score += 0.2
    if "b_melo" in roles:
        score += 0.15
    if "sabi" in roles or "dai_sabi" in roles:
        score += 0.2
    if "dai_sabi" in roles:
        score += 0.15
    if "compression" in phrase_roles and "release" in phrase_roles:
        score += 0.15

    ignition = profile.get("title_ignition_style", "hidden")
    if ignition in {"immediate", "delayed", "reframing"}:
        score += 0.15

    compression = profile.get("modern_compression_bias", "low")
    if compression in {"medium", "high"}:
        score += 0.1
    return round(min(1.0, score), 2)


def section_candidate_score(
    plan: dict[str, Any],
    card: dict[str, Any],
    section_lines: list[str],
) -> float:
    if not section_lines:
        return -999.0

    section = card["section"]
    text = " ".join(section_lines)
    score = 0.0
    ant_mode = str(plan.get("primary_mode", "")).strip() == "anthemic_cinematic"

    required = [item for item in card.get("required_motifs", [])[:3] if item]
    conditioning_atoms = [
        item
        for item in unique_preserve_order(card.get("conditioning_atoms", [])[:4])
        if item and item not in required
    ]

    if ant_mode:
        score += sum(1.2 for item in required if motif_matches_text(item, text))
    else:
        score += sum(1.2 for item in required if item in text)
    score += sum(0.45 for item in conditioning_atoms if item in text)

    target = int(card.get("line_target", len(section_lines)))
    score += max(0.0, 1.0 - abs(len(section_lines) - target) * 0.25)

    repeated_lines = sum(max(0, count - 1) for count in Counter(section_lines).values())
    score -= repeated_lines * 0.4

    if section.startswith("chorus"):
        hook = str(plan.get("hook_blueprint", {}).get("core_text", "")).strip()
        if hook and section_lines[0] == hook:
            score += 1.0
        if hook:
            hook_hits = text.count(hook)
            if hook_hits > 2:
                score -= (hook_hits - 2) * 0.45
        question_heads = [item for item in card.get("question_heads", []) if str(item).strip()]
        if question_heads and any("?" in line for line in section_lines):
            score += 0.45
        if str(plan.get("primary_mode", "")).strip() == "anthemic_cinematic":
            anthemic_markers = [
                "世界ごと",
                "未来",
                "音楽",
                "自由",
                "塗り替える",
                "連れ出せる",
                "引き上げる",
                "向こうへ",
            ]
            score += sum(0.14 for marker in anthemic_markers if marker in text)

    if section == "chorus_final":
        release_markers = plan.get("final_release_requirements", {}).get("release_markers", [])
        if any(marker in text for marker in release_markers):
            score += 0.8
        if any(marker in text for marker in ["ここから", "誤魔化さない", "引き受ける", "背負い直す"]):
            score += 0.35

    if section in {"pre_chorus", "pre_chorus_2", "bridge_rise"}:
        if any(marker in text for marker in ["だから", "それでも", "なのに", "ここから"]):
            score += 0.35
    if section == "pre_chorus_2":
        if "だからこそ" in text:
            score += 0.2
        if "隠さない" in text:
            score += 0.15

    if section.startswith("verse"):
        if any(marker in text for marker in ["生々しい", "露骨", "本性", "喉", "誤差"]):
            score += 0.35

    if section == "bridge_rise":
        if any(marker in text for marker in ["飲み込まない", "叫び返す", "声に変える"]):
            score += 0.25
        if "引き受ける" in text:
            score -= 0.1

    if section == "outro":
        if any(marker in text for marker in ["残る", "剥がれない", "見失わない", "取り落とさない", "間違えない"]):
            score += 0.45
        if "置き場を間違えない" in text:
            score += 0.2
        if "傷あとめいた" in text:
            score += 0.15

    return round(score, 3)


def line_candidate_score(
    card: dict[str, Any],
    line: str,
    *,
    line_index: int,
) -> float:
    if not line:
        return -999.0

    section = card["section"]
    required = [item for item in card.get("required_motifs", [])[:3] if item]
    conditioning_atoms = [
        item
        for item in unique_preserve_order(card.get("conditioning_atoms", [])[:5])
        if item and item not in required
    ]
    scaffold_markers = ["だけが", "だけは", "ばかり", "まま", "まだ", "みたい", "やっと"]
    concrete_markers = [
        "生々しい",
        "露骨",
        "本性",
        "喉",
        "脈",
        "誤差",
        "隠れない",
        "引き下がらない",
        "暴れる",
        "物差し",
        "凡庸",
        "正論",
        "ナイフ",
        "フロア",
        "踊り場",
        "左手",
        "蛇腹刃",
        "蛇火",
        "幕",
        "世界ごと",
        "音楽",
        "自由",
        "未来の拍",
        "塗り替える",
        "連れ出せる",
        "果てしない",
        "向こうへ",
    ]

    score = 0.0
    score += sum(1.0 for item in required if item in line)
    score += sum(0.3 for item in conditioning_atoms if item in line)
    score += sum(0.14 for item in concrete_markers if item in line)
    score -= sum(line.count(marker) * 0.08 for marker in scaffold_markers)
    if section.startswith("chorus") and required:
        hook_like = required[0]
        if line_index > 0 and hook_like:
            score -= line.count(hook_like) * 0.18
            if line.count(hook_like) > 1:
                score -= (line.count(hook_like) - 1) * 0.22

    if section == "verse_1":
        if line_index == 0 and "のに" in line:
            score += 0.25
        if line_index == 1:
            if "カルテ" in line:
                score += 0.72
            if "記した跡" in line:
                score += 0.12
            if "露骨" in line:
                score += 0.26
            if "生々しい" in line:
                score += 0.18
            if "正直" in line:
                score += 0.1
        if line_index == 2:
            if "片づけない" in line:
                score += 0.28
            if "名前" in line:
                score += 0.16
            if "説明" in line:
                score -= 0.05
        if line_index == 3:
            if "喉" in line:
                score += 0.4
            if "顔に残る" in line:
                score += 0.18
            if "隠れない" in line:
                score += 0.08
            if "残る" in line:
                score += 0.08
        if "故に" in line:
            score -= 0.16
    elif section == "verse_2":
        if line_index == 0 and any(marker in line for marker in ["ずれる", "正しい", "平気"]):
            score += 0.2
            if "ふりして" in line:
                score += 0.12
        if line_index == 1:
            if "輪郭" in line:
                score += 0.32
            if "壊れる" in line:
                score += 0.14
    if section.startswith("chorus"):
        if any(marker in line for marker in ["物差し", "凡庸", "フロア", "踊り場", "左手", "蛇腹刃", "幕"]):
            score += 0.18
    if section in {"pre_chorus", "pre_chorus_2", "bridge_rise"}:
        if any(marker in line for marker in ["追いつけない", "止まれない", "黙らせない", "暴れ", "牙", "幕"]):
            score += 0.12
            if "壊れていく" in line:
                score += 0.04
        if line_index == 3:
            if "喉" in line:
                score += 0.42
            if "上がる" in line:
                score += 0.16
            if "引き下がらない" in line:
                score += 0.04
        if "故に" in line:
            score -= 0.16
    elif section == "pre_chorus":
        if line_index == 0:
            if "輪郭" in line:
                score += 0.24
            if "寄せるたび" in line:
                score += 0.08
            if "きちんと" in line:
                score += 0.12
        if line_index == 2:
            if "追いつかない" in line:
                score += 0.25
            if "診断" in line:
                score += 1.0
    elif section == "pre_chorus_2":
        if line_index == 0:
            if "遅れた鼓動" in line:
                score += 0.24
            if "黙れない痛み" in line:
                score += 0.18
            if "噛みしめた声" in line:
                score -= 0.04
        if line_index == 1:
            if "だからこそ" in line:
                score += 0.24
            if "それでも" in line:
                score += 0.08
            if "なのに" in line:
                score += 0.06
            if "だけど" in line:
                score -= 0.02
            if "隠さない" in line:
                score += 0.18
        if line_index == 2 and any(marker in line for marker in ["喉", "暴れる"]):
            score += 0.25
    elif section == "chorus":
        if line_index == 0 and "折れない" in line:
            score += 0.4
        if line_index == 1:
            if "どうしたらいい" in line:
                score += 0.18
            if "どこへ捨てればいい" in line:
                score += 0.12
        if line_index == 2:
            if "誰に預ければいい" in line:
                score += 0.18
            if "何で決めればいい" in line:
                score += 0.1
        if line_index == 3:
            if "証明しようのない" in line:
                score += 0.18
            if "打ち返す" in line:
                score += 0.12
            if "また" in line:
                score += 0.08
            if "になる" in line:
                score -= 0.04
    elif section == "chorus_final":
        if line_index == 0 and "折れない" in line:
            score += 0.4
        if line_index == 1 and "まだ終わらない" in line:
            score += 0.28
        if line_index == 2:
            if "誤差のままでも" in line:
                score += 0.22
            if "答えにならなくても" in line:
                score += 0.16
            if "投げ捨てない" in line:
                score += 0.22
            if "抱え込む" in line:
                score += 0.12
        if line_index == 3:
            if "この声で背負い直す" in line:
                score += 0.32
            if "この喉で引き受ける" in line:
                score += 0.24
        if line_index == 4:
            if "誤魔化さない" in line:
                score += 0.28
            if "壊れたまま飲み込まない" in line:
                score += 0.22
            if "ここから先は" in line:
                score += 0.08
            if "ここから先を" in line:
                score += 0.16
            if "このまま引き受ける" in line:
                score -= 0.06
            if line.count("ここから") > 1:
                score -= 0.12
    elif section == "bridge_rise":
        if line_index == 2 and any(marker in line for marker in ["黙らない", "飲み込まない", "叫び返す"]):
            score += 0.3
        if "引き受ける" in line:
            score -= 0.08
    elif section == "outro":
        if any(marker in line for marker in ["置き場を間違えない", "見失わない", "取り落とさない", "剥がれない", "傷あとめいた"]):
            score += 0.25

    return round(score, 3)


def compose_section_lines_from_candidates(
    card: dict[str, Any],
    candidate_sections: list[list[str]],
) -> list[str] | None:
    usable = [lines for lines in candidate_sections if lines]
    if len(usable) < 2:
        return None

    expected_length = len(usable[0])
    if expected_length == 0 or any(len(lines) != expected_length for lines in usable):
        return None

    mixed_sections = {"verse_1", "verse_2", "pre_chorus", "pre_chorus_2", "chorus", "chorus_final", "bridge_rise", "outro"}
    if card["section"] not in mixed_sections:
        return None

    selected: list[str] = []
    for idx in range(expected_length):
        best_line = ""
        best_score = -999.0
        for lines in usable:
            line = lines[idx]
            score = line_candidate_score(card, line, line_index=idx)
            if score > best_score:
                best_score = score
                best_line = line
        if not best_line:
            return None
        selected.append(best_line)
    return selected


def build_bestof_candidate(
    plan: dict[str, Any],
    candidates: list[dict[str, Any]],
    ranked_critique_results: list[dict[str, Any]],
) -> dict[str, Any] | None:
    if str(plan.get("primary_mode", "")).strip() == "direct_emotional_pop":
        return None
    if len(candidates) < 2 or not ranked_critique_results:
        return None

    candidate_lookup = {candidate["candidate_id"]: candidate for candidate in candidates}
    ranked_candidates = [
        candidate_lookup[item["candidate_id"]]
        for item in ranked_critique_results
        if item["candidate_id"] in candidate_lookup
    ]
    if len(ranked_candidates) < 2:
        return None

    critic_totals = {
        item["candidate_id"]: float(item.get("scores", {}).get("total", 0.0))
        for item in ranked_critique_results
    }
    section_maps = {
        candidate["candidate_id"]: {section: lines for section, lines in extract_section_blocks(candidate["markdown"])}
        for candidate in ranked_candidates
    }

    top_candidate = ranked_candidates[0]
    mixed_sections = {"verse_1", "verse_2", "pre_chorus", "pre_chorus_2", "chorus", "chorus_final", "bridge_rise", "outro"}
    merged_title = top_candidate.get("title") or plan.get("title", "Untitled")
    
    # Preserve Metadata from Top Candidate
    metadata_lines = []
    style_keywords = ["Genre:", "Tempo:", "Vocal:", "Instruments:", "Beat Concept:", "Mood & Atmosphere:", "Theme:"]
    for m_line in top_candidate["markdown"].splitlines()[:20]: # Only check top of file
        ls = m_line.strip()
        if ls.startswith("###") or any(ls.startswith(kw) for kw in style_keywords):
            metadata_lines.append(m_line)
        elif ls.startswith("# ") or ls.startswith("["):
            break # Stop at first lyric content
            
    lines = []
    if metadata_lines:
        lines.extend(metadata_lines)
        lines.append("")
        
    lines.extend([f"# {merged_title}", ""])
    chosen_any = False
    for card in plan["section_cards"]:
        section = card["section"]
        if section not in mixed_sections:
            best_lines = section_maps[top_candidate["candidate_id"]].get(section, [])
            if not best_lines:
                continue
            chosen_any = True
            lines.append(f"[{section}]")
            lines.extend(best_lines)
            lines.append("")
            continue

        section_ranked_candidates = sorted(
            ranked_candidates,
            key=lambda candidate: (
                section_candidate_score(
                    plan,
                    card,
                    section_maps[candidate["candidate_id"]].get(section, []),
                ),
                critic_totals.get(candidate["candidate_id"], 0.0),
            ),
            reverse=True,
        )
        line_mix_candidates = ranked_candidates
        candidate_sections = [
            section_maps[candidate["candidate_id"]].get(section, [])
            for candidate in line_mix_candidates
        ]
        best_lines: list[str] | None = compose_section_lines_from_candidates(card, candidate_sections)
        best_score = -999.0
        if best_lines is None:
            for candidate in section_ranked_candidates:
                section_lines = section_maps[candidate["candidate_id"]].get(section, [])
                score = section_candidate_score(plan, card, section_lines)
                if score > best_score:
                    best_score = score
                    best_lines = section_lines
        if not best_lines:
            continue
        chosen_any = True
        lines.append(f"[{section}]")
        lines.extend(best_lines)
        lines.append("")

    if not chosen_any:
        return None

    markdown_text = "\n".join(lines).strip() + "\n"
    return {
        "candidate_id": f"{plan['track_id']}-candidate-bestof",
        "variant_index": None,
        "title": merged_title,
        "markdown": markdown_text,
    }


def critique_candidate(plan: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    markdown_text = candidate["markdown"]
    
    # [PHASE 8] Zero-Tolerance Linguistic Hardening
    is_contaminated = looks_corrupted_text(markdown_text)
    
    scores = {
        "motif_coverage": motif_coverage_score(plan, markdown_text),
        "plan_alignment": plan_alignment_score(plan, markdown_text),
        "hook_control": hook_control_score(plan, markdown_text),
        "specificity": specificity_score(plan, markdown_text),
        "novelty": novelty_score(markdown_text),
        "final_release": final_release_score(plan, markdown_text),
        "jp_hook_force": jp_hook_force_score(candidate["title"], markdown_text),
        "jp_section_flow": jp_section_flow_score(markdown_text, candidate["title"]),
        "mastery_alignment": validate_against_blueprint(
            markdown_text.splitlines(), 
            "Chorus", 
            mode_id=plan.get("primary_mode", "universal")
        ).get("total_mastery_score", 0.0),
    }
    
    if is_contaminated:
        total = 0.0
    else:
        total = round(
            scores["motif_coverage"] * 20
            + scores["plan_alignment"] * 16
            + scores["hook_control"] * 10
            + scores["specificity"] * 12
            + scores["novelty"] * 8
            + scores["final_release"] * 6
            + scores["jp_hook_force"] * 6
            + scores["jp_section_flow"] * 4
            + scores["mastery_alignment"] * 18,
            2,
        )
        
    summary = []
    if is_contaminated:
        summary.append("CRITICAL: Linguistic leakage detected (Hangul characters found)")
    if scores["specificity"] < 0.6:
        summary.append("surface imagery is still too abstract")
    if scores["novelty"] < 0.6:
        summary.append("phrasing still feels template-heavy")
    if scores["plan_alignment"] < 0.75:
        summary.append("section motifs are not landing consistently")
    if scores["final_release"] < 0.5:
        summary.append("final chorus does not release strongly enough")
    if scores["jp_hook_force"] < 0.65:
        summary.append("hook phrasing still lacks Japanese copy-force")
    if scores["jp_section_flow"] < 0.65:
        summary.append("A-melo / B-melo / Sabi flow still feels weak")
        
    if not summary:
        summary.append("best candidate in this set; still review humanly before reuse")
        
    return {
        "candidate_id": candidate["candidate_id"],
        "title": candidate["title"],
        "scores": {**scores, "total": total},
        "critic_notes": summary,
    }


def render_run_report(run_manifest: dict[str, Any]) -> str:
    lines = [
        f"# Songwriter V2 Run: {run_manifest['track_id']}",
        "",
        f"- Source JSONL: `{run_manifest['source_jsonl']}`",
        f"- Candidate count: `{run_manifest['candidate_count']}`",
        f"- Winning candidate: `{run_manifest['selected_candidate_id']}`",
        f"- Winning score: `{run_manifest['selected_score']}`",
        "",
        "## Critic Results",
        "",
    ]
    for critique in run_manifest["critic_results"]:
        scores = critique["scores"]
        lines.extend(
            [
                f"### {critique['candidate_id']}",
                f"- Title: `{critique['title']}`",
                f"- Total: `{scores['total']}`",
                f"- Motif coverage: `{scores['motif_coverage']}`",
                f"- Plan alignment: `{scores['plan_alignment']}`",
                f"- Hook control: `{scores['hook_control']}`",
                f"- Specificity: `{scores['specificity']}`",
                f"- Novelty: `{scores['novelty']}`",
                f"- Final release: `{scores['final_release']}`",
                f"- JP hook force: `{scores['jp_hook_force']}`",
                f"- JP section flow: `{scores['jp_section_flow']}`",
                f"- Notes: {'; '.join(critique['critic_notes'])}",
                "",
            ]
        )
    return "\n".join(lines)


def run_songwriter_v2(
    source_jsonl: Path,
    *,
    track_id: str | None,
    output_dir: Path,
    candidate_count: int,
    include_history: bool = True,
) -> dict[str, Any]:
    records = load_jsonl(source_jsonl)
    if not records:
        raise ValueError(f"No records found in {source_jsonl}")
    selected_track_id = track_id or resolve_default_track_id(records)
    record = choose_record(records, selected_track_id)

    plan = build_song_plan(record)
    prompt_package = build_prompt_package(plan)
    candidates = [render_candidate(plan, variant_index=index) for index in range(candidate_count)]
    if include_history:
        historical_candidates = load_historical_candidates(plan["track_id"], output_dir)
        if historical_candidates:
            candidates.extend(historical_candidates)
    candidates = dedupe_candidates(candidates)
    base_critique_results = [critique_candidate(plan, candidate) for candidate in candidates]
    base_critique_results.sort(key=lambda item: item["scores"]["total"], reverse=True)
    bestof_candidate = build_bestof_candidate(plan, candidates, base_critique_results)
    if bestof_candidate:
        candidates.append(bestof_candidate)
        candidates = dedupe_candidates(candidates)

    critic_results = [critique_candidate(plan, candidate) for candidate in candidates]
    critic_results.sort(
        key=lambda item: (
            item["scores"]["total"],
            1 if str(item.get("candidate_id", "")).endswith("bestof") else 0,
        ),
        reverse=True,
    )
    winner = critic_results[0]
    winner_candidate = next(candidate for candidate in candidates if candidate["candidate_id"] == winner["candidate_id"])

    output_dir.mkdir(parents=True, exist_ok=True)
    plan_path = write_utf8_json(output_dir / "plan.json", plan)
    prompt_path = write_utf8_json(output_dir / "prompt_package.json", prompt_package)
    candidates_path = write_utf8_json(
        output_dir / "candidates.json",
        {
            "track_id": plan["track_id"],
            "candidate_count": candidate_count,
            "historical_candidate_count": sum(1 for candidate in candidates if candidate.get("source_run_dir")),
            "candidates": [{"candidate_id": candidate["candidate_id"], "title": candidate["title"]} for candidate in candidates],
        },
    )
    critique_path = write_utf8_json(output_dir / "critic_results.json", {"critic_results": critic_results})
    for candidate in candidates:
        write_utf8_text(output_dir / f"{candidate['candidate_id']}.md", candidate["markdown"], trailing_newline=False)
    winner_path = write_utf8_text(output_dir / "selected_lyric.md", winner_candidate["markdown"], trailing_newline=False)

    manifest = {
        "schema_version": "1.0",
        "track_id": plan["track_id"],
        "artist_id": plan["artist_id"],
        "source_jsonl": str(source_jsonl),
        "output_dir": str(output_dir),
        "candidate_count": candidate_count,
        "include_history": include_history,
        "selected_candidate_id": winner["candidate_id"],
        "selected_score": winner["scores"]["total"],
        "plan_path": str(plan_path),
        "prompt_package_path": str(prompt_path),
        "candidates_path": str(candidates_path),
        "critic_results_path": str(critique_path),
        "selected_lyric_path": str(winner_path),
        "critic_results": critic_results,
    }
    report_path = write_utf8_text(output_dir / "run_report.md", render_run_report(manifest), trailing_newline=False)
    manifest["run_report_path"] = str(report_path)
    manifest_path = write_utf8_json(output_dir / "run_manifest.json", manifest)
    manifest["manifest_path"] = str(manifest_path)
    return manifest
