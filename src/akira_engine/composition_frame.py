from __future__ import annotations

import re
from typing import Any

from .lexical_family_bank import classify_term_family
from .lyric_utils import contains_japanese, extract_japanese_lexical_atoms, safe_text
from .section_evidence_bank import build_section_evidence_bank


_LOW_SIGNAL_CORPUS_TERMS = {
    "平日",
    "休日",
    "毎日",
    "平日だけ",
    "休日だけ",
}


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        text = safe_text(value)
        if not text or text in seen:
            continue
        seen.add(text)
        out.append(text)
    return out


def _merge_list(primary: list[str], secondary: list[str], *, limit: int) -> list[str]:
    return _unique(list(primary or []) + list(secondary or []))[:limit]


def _record_artist_id(record: dict[str, Any]) -> str:
    return safe_text(record.get("track_identity", {}).get("artist_id"))


def _record_title_terms(record: dict[str, Any]) -> list[str]:
    identity = record.get("track_identity", {}) if isinstance(record.get("track_identity", {}), dict) else {}
    lyric = record.get("lyric_ground_truth", {}) if isinstance(record.get("lyric_ground_truth", {}), dict) else {}
    song_intent = record.get("song_intent", {}) if isinstance(record.get("song_intent", {}), dict) else {}
    section_analysis = record.get("section_analysis", []) if isinstance(record.get("section_analysis", []), list) else []
    section_values: list[Any] = []
    for entry in section_analysis:
        if not isinstance(entry, dict):
            continue
        section_values.extend(entry.get("vocabulary_focus", []))
        section_values.append(entry.get("narrative_job"))
    values = [
        identity.get("title"),
        identity.get("title_core"),
        *lyric.get("hook_lines", []),
        *lyric.get("question_lines", []),
        *song_intent.get("key_motifs", []),
        *section_values,
    ]
    output = _unique(
        [safe_text(value) for value in values if safe_text(value)]
        + extract_japanese_lexical_atoms(values, limit=24)
    )
    return output


def _term_overlaps_lexicon(term: str, lexicon: set[str]) -> bool:
    text = safe_text(term)
    if not text or not lexicon:
        return False
    for existing in lexicon:
        marker = safe_text(existing)
        if not marker:
            continue
        if text == marker:
            return True
        if text in marker or marker in text:
            return True
    return False


def _collect_bank_lexicon(bank: dict[str, Any]) -> set[str]:
    values: list[str] = []
    values.extend(bank.get("global_motifs", []) or [])
    values.extend(bank.get("global_imagery", []) or [])
    for payload in (bank.get("sections") or {}).values():
        if not isinstance(payload, dict):
            continue
        values.extend(payload.get("required_motifs", []) or [])
        values.extend(payload.get("required_imagery", []) or [])
        values.extend(payload.get("imagery_focus", []) or [])
        values.append(payload.get("scene"))
    return {
        safe_text(value)
        for value in values
        if safe_text(value)
    }


def _is_low_signal_corpus_term(value: str) -> bool:
    text = safe_text(value)
    if not text:
        return True
    if text in _LOW_SIGNAL_CORPUS_TERMS:
        return True
    if re.fullmatch(r"(平日|休日|毎日)(だけ|しか)?", text):
        return True
    return False


def _prune_bank_terms(
    bank: dict[str, Any],
    banned_terms: set[str],
    *,
    artist_lexicon: set[str] | None = None,
    artist_families: set[str] | None = None,
) -> dict[str, Any]:
    if not bank:
        return bank

    def is_banned(value: str) -> bool:
        text = safe_text(value)
        if not text:
            return False
        for banned in banned_terms:
            marker = safe_text(banned)
            if not marker:
                continue
            if text == marker:
                return True
            if text in marker or marker in text:
                return True
        return False

    artist_lexicon = artist_lexicon or set()
    artist_families = artist_families or set()

    def keep(values: list[str], limit: int) -> list[str]:
        kept: list[str] = []
        for value in _unique(list(values or [])):
            text = safe_text(value)
            if not text or is_banned(text):
                continue
            if artist_lexicon:
                if _is_low_signal_corpus_term(text):
                    continue
                family = classify_term_family(text)
                if not _term_overlaps_lexicon(text, artist_lexicon) and (
                    not family or family not in artist_families
                ):
                    continue
            kept.append(value)
            if len(kept) >= limit:
                break
        return kept

    def keep_goals(values: list[str], limit: int) -> list[str]:
        return [
            value
            for value in _unique(list(values or []))
            if safe_text(value)
            and contains_japanese(safe_text(value))
            and not is_banned(value)
        ][:limit]

    sections = {}
    for section_name, payload in (bank.get("sections") or {}).items():
        cleaned = dict(payload)
        cleaned["narrative_goals"] = keep_goals(payload.get("narrative_goals", []), 4)
        cleaned["required_motifs"] = keep(payload.get("required_motifs", []), 8)
        cleaned["required_imagery"] = keep(payload.get("required_imagery", []), 6)
        cleaned["imagery_focus"] = keep(payload.get("imagery_focus", []), 8)
        scene = safe_text(payload.get("scene"))
        cleaned["scene"] = ""
        if scene and not is_banned(scene):
            if not artist_lexicon or (
                not _is_low_signal_corpus_term(scene)
                and (
                    _term_overlaps_lexicon(scene, artist_lexicon)
                    or (
                        classify_term_family(scene)
                        and classify_term_family(scene) in artist_families
                    )
                )
            ):
                cleaned["scene"] = scene
        sections[section_name] = cleaned

    cleaned_bank = dict(bank)
    cleaned_bank["global_motifs"] = keep(bank.get("global_motifs", []), 12)
    cleaned_bank["global_imagery"] = keep(bank.get("global_imagery", []), 12)
    cleaned_bank["sections"] = sections
    return cleaned_bank


def _merge_section_payload(
    artist_payload: dict[str, Any] | None,
    corpus_payload: dict[str, Any] | None,
) -> dict[str, Any]:
    artist_payload = artist_payload or {}
    corpus_payload = corpus_payload or {}
    section_name = safe_text(artist_payload.get("section") or corpus_payload.get("section"))
    line_target = int(
        artist_payload.get("line_target")
        or corpus_payload.get("line_target")
        or 0
    )
    abstraction_candidates = [
        float(value)
        for value in [
            artist_payload.get("abstraction_ceiling"),
            corpus_payload.get("abstraction_ceiling"),
        ]
        if value not in (None, "")
    ]
    return {
        "section": section_name,
        "function_hint": safe_text(
            artist_payload.get("function_hint")
            or corpus_payload.get("function_hint")
        ),
        "behavior_prior": artist_payload.get("behavior_prior") or corpus_payload.get("behavior_prior") or {},
        "narrative_goals": _merge_list(
            list(artist_payload.get("narrative_goals", [])),
            list(corpus_payload.get("narrative_goals", [])),
            limit=4,
        ),
        "required_motifs": _merge_list(
            list(artist_payload.get("required_motifs", [])),
            list(corpus_payload.get("required_motifs", [])),
            limit=8,
        ),
        "required_imagery": _merge_list(
            list(artist_payload.get("required_imagery", [])),
            list(corpus_payload.get("required_imagery", [])),
            limit=6,
        ),
        "imagery_focus": _merge_list(
            list(artist_payload.get("imagery_focus", [])),
            list(corpus_payload.get("imagery_focus", [])),
            limit=8,
        ),
        "line_target": line_target,
        "cadence_target": safe_text(
            artist_payload.get("cadence_target")
            or corpus_payload.get("cadence_target")
        ),
        "abstraction_ceiling": min(abstraction_candidates) if abstraction_candidates else 0.18,
        "title_drop_policy": safe_text(
            artist_payload.get("title_drop_policy")
            or corpus_payload.get("title_drop_policy")
        ),
        "title_drop_roles": _merge_list(
            list(artist_payload.get("title_drop_roles", [])),
            list(corpus_payload.get("title_drop_roles", [])),
            limit=3,
        ),
        "phrase_energy_roles": _merge_list(
            list(artist_payload.get("phrase_energy_roles", [])),
            list(corpus_payload.get("phrase_energy_roles", [])),
            limit=3,
        ),
        "hook_pressure": safe_text(
            artist_payload.get("hook_pressure")
            or corpus_payload.get("hook_pressure")
            or "medium"
        ),
        "evidence_track_ids": _merge_list(
            list(artist_payload.get("evidence_track_ids", [])),
            list(corpus_payload.get("evidence_track_ids", [])),
            limit=12,
        ),
        "source_count": int(artist_payload.get("source_count", 0) or 0)
        + int(corpus_payload.get("source_count", 0) or 0),
        "artist_source_count": int(artist_payload.get("source_count", 0) or 0),
        "corpus_source_count": int(corpus_payload.get("source_count", 0) or 0),
    }


def build_composition_frame(
    *,
    artist_records: list[dict[str, Any]],
    mode_support_records: list[dict[str, Any]],
    mode_id: str,
    behavior_priors: dict[str, Any] | None = None,
) -> dict[str, Any]:
    artist_bank = build_section_evidence_bank(
        artist_records,
        mode_id=mode_id,
        behavior_priors=behavior_priors,
    )
    corpus_bank = build_section_evidence_bank(
        mode_support_records,
        mode_id=mode_id,
        behavior_priors=behavior_priors,
    )
    artist_lexicon = _collect_bank_lexicon(artist_bank)
    artist_families = {
        family
        for term in artist_lexicon
        for family in [classify_term_family(term)]
        if family
    }
    home_artists = {
        _record_artist_id(record)
        for record in artist_records
        if _record_artist_id(record)
    }
    foreign_title_terms = {
        safe_text(term)
        for record in mode_support_records
        if _record_artist_id(record) and _record_artist_id(record) not in home_artists
        for term in _record_title_terms(record)
        if safe_text(term)
    }
    corpus_bank = _prune_bank_terms(
        corpus_bank,
        foreign_title_terms,
        artist_lexicon=artist_lexicon,
        artist_families=artist_families,
    )

    merged_sections: dict[str, dict[str, Any]] = {}
    section_names = _unique(
        list((artist_bank.get("sections") or {}).keys())
        + list((corpus_bank.get("sections") or {}).keys())
    )
    for section_name in section_names:
        merged_sections[section_name] = _merge_section_payload(
            (artist_bank.get("sections") or {}).get(section_name),
            (corpus_bank.get("sections") or {}).get(section_name),
        )

    artist_hook = artist_bank.get("hook_blueprint", {}) or {}
    corpus_hook = corpus_bank.get("hook_blueprint", {}) or {}
    merged_hook = {
        "hook_density": safe_text(artist_hook.get("hook_density") or corpus_hook.get("hook_density") or "medium"),
        "title_ignition_style": safe_text(
            artist_hook.get("title_ignition_style")
            or corpus_hook.get("title_ignition_style")
            or "direct"
        ),
        "chorus_line_target": int(
            artist_hook.get("chorus_line_target")
            or corpus_hook.get("chorus_line_target")
            or 4
        ),
        "hook_line_target": int(
            artist_hook.get("hook_line_target")
            or corpus_hook.get("hook_line_target")
            or 2
        ),
        "repetition_pressure": safe_text(
            artist_hook.get("repetition_pressure")
            or corpus_hook.get("repetition_pressure")
            or "medium"
        ),
    }

    return {
        "planning_basis": "corpus_driven_artist_biased",
        "mode_id": safe_text(mode_id),
        "artist_record_count": int(artist_bank.get("record_count", 0) or 0),
        "mode_record_count": int(corpus_bank.get("record_count", 0) or 0),
        "artist_track_ids": list(artist_bank.get("selected_track_ids", [])),
        "mode_track_ids": list(corpus_bank.get("selected_track_ids", [])),
        "merged_track_ids": _merge_list(
            list(artist_bank.get("selected_track_ids", [])),
            list(corpus_bank.get("selected_track_ids", [])),
            limit=24,
        ),
        "artist_global_motifs": list(artist_bank.get("global_motifs", [])),
        "mode_global_motifs": list(corpus_bank.get("global_motifs", [])),
        "artist_global_imagery": list(artist_bank.get("global_imagery", [])),
        "mode_global_imagery": list(corpus_bank.get("global_imagery", [])),
        "foreign_title_terms_filtered": sorted(foreign_title_terms),
        "artist_bank": artist_bank,
        "mode_bank": corpus_bank,
        "merged_bank": {
            "available": bool(merged_sections),
            "mode_id": safe_text(mode_id),
            "record_count": int(artist_bank.get("record_count", 0) or 0)
            + int(corpus_bank.get("record_count", 0) or 0),
            "selected_track_ids": _merge_list(
                list(artist_bank.get("selected_track_ids", [])),
                list(corpus_bank.get("selected_track_ids", [])),
                limit=24,
            ),
            "global_motifs": _merge_list(
                list(artist_bank.get("global_motifs", [])),
                list(corpus_bank.get("global_motifs", [])),
                limit=12,
            ),
            "global_imagery": _merge_list(
                list(artist_bank.get("global_imagery", [])),
                list(corpus_bank.get("global_imagery", [])),
                limit=12,
            ),
            "hook_blueprint": merged_hook,
            "behavior_priors": dict(behavior_priors or {}),
            "sections": merged_sections,
        },
        "behavior_priors": dict(behavior_priors or {}),
    }
