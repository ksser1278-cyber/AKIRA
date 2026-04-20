from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from dataclasses import replace
from pathlib import Path
from typing import Any

from .critic.mod import CriticResult, run_critic_stage
from .lexical_family_bank import classify_term_family
from .lyric_api_adapter import generate_candidate_via_api
from .lyric_behavior_priors import load_lyric_behavior_priors
from .lyric_utils import contains_bad_script, contains_japanese, safe_text, unique_preserve_order
from .promotion.mod import run_promotion_stage
from .prompt_package_builder import build_prompt_package
from .renderer.mod import run_renderer_stage
from .songwriter_io import candidate_content_roots, load_conditioning_records, load_representative_demo_profile


ENGINE_TYPE = "corpus_driven_proposition_engine"
SCHEMA_VERSION = "3.0"

_DARK_CUTE_MODE_PROFILE: dict[str, Any] = {
    "mode_id": "dark_cute_breakdown",
    "form_shortlist": ["compressed_hook", "hybrid_release"],
    "singability_profile": {
        "hook_mora_band": [8, 12],
        "verse_mora_band": [7, 11],
        "repeatability_target": "high",
        "vowel_flow_target": "front_loaded_clear",
        "oral_friction_budget": "medium",
    },
    "energy_curve": [
        {"section": "intro", "pressure_stage": "low"},
        {"section": "verse_1", "pressure_stage": "set"},
        {"section": "pre_chorus", "pressure_stage": "rising"},
        {"section": "chorus", "pressure_stage": "impact"},
        {"section": "verse_2", "pressure_stage": "heated"},
        {"section": "pre_chorus_2", "pressure_stage": "surging"},
        {"section": "bridge", "pressure_stage": "withheld"},
        {"section": "chorus_final", "pressure_stage": "overload"},
        {"section": "outro", "pressure_stage": "residual"},
    ],
    "preferred_families": ["body", "collapse", "childhood", "architectural", "mechanical", "silence"],
    "fallback_terms": {
        "body": ["体温", "傷", "鼓動", "喉元", "皮膚", "爪"],
        "collapse": ["ひび", "落下", "崩壊", "断線", "軋み", "沈下"],
        "childhood": ["キャンディ", "遊園地", "おもちゃ", "まばたき", "魔法", "教室"],
        "architectural": ["部屋", "暗室", "教室", "廊下", "窓", "床"],
        "mechanical": ["静電気", "点滅", "反射", "通知", "ノイズ", "モニタリング"],
        "silence": ["沈黙", "余熱", "残り香", "温度", "影", "気配"],
    },
    "listener_position": "self_address",
}

_ARTIST_GRAMMAR_BIAS: dict[str, dict[str, Any]] = {
    "maretu": {
        "hook_compression": "high",
        "line_attack": "hard",
        "cadence_preference": ["compressed", "explosive", "rising"],
        "lexical_roughness": "high",
        "repeat_tolerance": "tight",
        "title_return_tolerance": "medium",
    },
    "deco27": {
        "hook_compression": "balanced",
        "line_attack": "balanced",
        "cadence_preference": ["balanced", "rising", "compressed"],
        "lexical_roughness": "medium",
        "repeat_tolerance": "medium",
        "title_return_tolerance": "medium",
    },
    "pinocchiop": {
        "hook_compression": "medium_high",
        "line_attack": "pointed",
        "cadence_preference": ["compressed", "balanced", "suspended"],
        "lexical_roughness": "medium",
        "repeat_tolerance": "medium",
        "title_return_tolerance": "high",
    },
    "kanaria": {
        "hook_compression": "very_high",
        "line_attack": "sharp",
        "cadence_preference": ["compressed", "rising", "explosive"],
        "lexical_roughness": "medium_high",
        "repeat_tolerance": "tight",
        "title_return_tolerance": "medium_high",
    },
    "default": {
        "hook_compression": "balanced",
        "line_attack": "balanced",
        "cadence_preference": ["balanced", "compressed"],
        "lexical_roughness": "medium",
        "repeat_tolerance": "medium",
        "title_return_tolerance": "medium",
    },
}

_FORM_VARIANTS: dict[str, dict[str, Any]] = {
    "compressed_hook": {
        "section_order": [
            "intro",
            "verse_1",
            "pre_chorus",
            "chorus",
            "verse_2",
            "pre_chorus_2",
            "bridge",
            "chorus_final",
            "outro",
        ],
        "line_targets": [4, 4, 2, 4, 4, 2, 2, 6, 3],
    },
    "hybrid_release": {
        "section_order": [
            "intro",
            "verse_1",
            "pre_chorus",
            "chorus",
            "verse_2",
            "bridge",
            "chorus_final",
            "outro",
        ],
        "line_targets": [4, 4, 3, 5, 4, 3, 5, 3],
    },
}

_SECTION_ROLE_MAP = {
    "intro": "atmosphere_only",
    "verse_1": "world_placement",
    "pre_chorus": "pressure_ramp",
    "chorus": "proposition_delivery",
    "verse_2": "pressure_intensification",
    "pre_chorus_2": "faster_pressure_ramp",
    "bridge": "suspended_withholding",
    "chorus_final": "irreversible_release",
    "outro": "residue",
}

_SEMANTIC_CARRY_MAP = {
    "intro": "scene_seed",
    "verse_1": "field_seed",
    "pre_chorus": "pressure_lift",
    "chorus": "proposition_core",
    "verse_2": "same_field_escalated",
    "pre_chorus_2": "same_field_faster",
    "bridge": "withheld_view",
    "chorus_final": "release_overload",
    "outro": "residue_trace",
}

_HOOK_DEPENDENCY_MAP = {
    "intro": "none",
    "verse_1": "low",
    "pre_chorus": "foreshadow",
    "chorus": "core",
    "verse_2": "echo",
    "pre_chorus_2": "accelerate",
    "bridge": "withhold",
    "chorus_final": "overload",
    "outro": "residue",
}

_DEFAULT_CADENCE_BY_SECTION = {
    "intro": "balanced",
    "verse_1": "balanced",
    "pre_chorus": "rising",
    "chorus": "compressed",
    "verse_2": "balanced",
    "pre_chorus_2": "rising",
    "bridge": "suspended",
    "chorus_final": "explosive",
    "outro": "held",
}

_DEFAULT_REPETITION_BY_SECTION = {
    "intro": 0,
    "verse_1": 0,
    "pre_chorus": 1,
    "chorus": 2,
    "verse_2": 0,
    "pre_chorus_2": 1,
    "bridge": 0,
    "chorus_final": 2,
    "outro": 0,
}

_TITLE_RETURN_POLICY_BY_SECTION = {
    "intro": "withhold",
    "verse_1": "withhold",
    "pre_chorus": "withhold",
    "chorus": "primary",
    "verse_2": "withhold",
    "pre_chorus_2": "withhold",
    "bridge": "withhold",
    "chorus_final": "primary",
    "outro": "sparse",
}

_PROPOSITION_TEMPLATES: list[dict[str, Any]] = [
    {
        "archetype_kind": "obsessive_return",
        "hook_density_target": "high",
        "title_return_policy": "primary",
        "escalation_phrase": "離せないまま深く沈む",
        "release_phrase": "壊れながらも戻れない",
    },
    {
        "archetype_kind": "confessional_hold",
        "hook_density_target": "medium",
        "title_return_policy": "anchor",
        "escalation_phrase": "やさしい顔では抱えきれない",
        "release_phrase": "抱えたまま落ちていく",
    },
    {
        "archetype_kind": "dependency_spiral",
        "hook_density_target": "medium",
        "title_return_policy": "anchor",
        "escalation_phrase": "甘さの底でもまだ逃げられない",
        "release_phrase": "依存のままで崩れていく",
    },
    {
        "archetype_kind": "rupture_assertion",
        "hook_density_target": "high",
        "title_return_policy": "primary",
        "escalation_phrase": "ひびごと喉元まで裂けていく",
        "release_phrase": "衝動のままで踏み抜いていく",
    },
]


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            records.append(payload)
    return records


def _write_json(path: Path, payload: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def _write_text(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")
    return path


def _discover_form_family_assets(
    project_root: Path,
    catalog_name: str = "calibration_v1",
) -> tuple[dict[str, Any], list[dict[str, Any]], Path]:
    for content_root in candidate_content_roots(project_root.resolve()):
        catalog_path = content_root / "datasets" / "training" / "form_families" / catalog_name / "form_family_catalog.json"
        assignments_path = content_root / "datasets" / "training" / "form_families" / catalog_name / "track_form_assignments.jsonl"
        if catalog_path.exists() and assignments_path.exists():
            return _load_json(catalog_path), _load_jsonl(assignments_path), catalog_path
    raise FileNotFoundError(f"Form family assets not found for catalog '{catalog_name}'")


def _mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return round(sum(values) / len(values), 2)


def _top(values: list[str], default: str = "") -> str:
    counts = Counter(value for value in values if safe_text(value))
    if not counts:
        return default
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))[0][0]


def _looks_like_low_signal(text: str) -> bool:
    compact = safe_text(text).replace(" ", "")
    if not compact:
        return True
    if len(compact) <= 1:
        return True
    if re.fullmatch(r"[\u3040-\u309f]{1,2}", compact):
        return True
    blocked = {"こと", "もの", "だけ", "まだ", "また", "そこ", "ここ", "誰か", "誰に", "場所", "言葉", "気持ち"}
    return compact in blocked


def _normalize_corpus_surface(value: Any) -> str:
    text = safe_text(value)
    if not text:
        return ""
    text = re.sub(r"\s*\([^)]*[A-Za-z][^)]*\)", "", text)
    text = re.sub(r"[\"'`]+", "", text)
    text = re.sub(r"\s+", " ", text).strip(" /-_,;:")
    return text.strip()


def _sanitize_japanese_term(value: Any) -> str:
    text = _normalize_corpus_surface(value)
    if not text:
        return ""
    if not contains_japanese(text) or contains_bad_script(text):
        return ""
    compact = text.replace(" ", "")
    if len(compact) > 18:
        return ""
    if _looks_like_low_signal(text):
        return ""
    return text


def _looks_like_surface_phrase(text: str) -> bool:
    compact = safe_text(text).replace(" ", "")
    if not compact:
        return True
    if compact in {"ぶっ壊して", "壊していく", "ぶっ壊していく"}:
        return True
    if len(compact) < 4:
        return False
    return any(
        compact.endswith(ending)
        for ending in (
            "して",
            "していく",
            "してる",
            "ていく",
            "れていく",
            "される",
            "られる",
            "なくなる",
            "になる",
        )
    )


def _sanitize_surface_term(value: Any) -> str:
    text = _sanitize_japanese_term(value)
    if not text:
        return ""
    if _looks_like_surface_phrase(text):
        return ""
    return text


def _japanese_terms(values: list[Any]) -> list[str]:
    terms: list[str] = []
    for value in values:
        text = _sanitize_japanese_term(value)
        if text and text not in terms:
            terms.append(text)
    return terms


def _surface_terms(values: list[Any]) -> list[str]:
    terms: list[str] = []
    for value in values:
        text = _sanitize_surface_term(value)
        if text and text not in terms:
            terms.append(text)
    return terms


def _record_title(record: dict[str, Any]) -> str:
    identity = record.get("track_identity", {}) if isinstance(record.get("track_identity"), dict) else {}
    return _sanitize_japanese_term(identity.get("title_core")) or _sanitize_japanese_term(identity.get("title"))


def _record_terms(record: dict[str, Any]) -> list[str]:
    song_intent = record.get("song_intent", {}) if isinstance(record.get("song_intent"), dict) else {}
    section_analysis = record.get("section_analysis", []) if isinstance(record.get("section_analysis"), list) else []
    values: list[Any] = []
    values.extend([_record_title(record)])
    values.extend(song_intent.get("key_motifs", []))
    for section in section_analysis:
        if isinstance(section, dict):
            values.extend(section.get("vocabulary_focus", []))
    return _surface_terms(values)


def _record_family_votes(record: dict[str, Any]) -> list[str]:
    families: list[str] = []
    for term in _record_terms(record):
        family = safe_text(classify_term_family(term))
        if family:
            families.append(family)
    return families


def _record_signal_score(record: dict[str, Any]) -> int:
    title = _record_title(record)
    score = 3 if title else 0
    score += len(_record_terms(record))
    song_intent = record.get("song_intent", {}) if isinstance(record.get("song_intent"), dict) else {}
    if safe_text(song_intent.get("emotional_thesis")):
        score += 2
    narrative_role = song_intent.get("narrative_role", [])
    if isinstance(narrative_role, list):
        score += len([value for value in narrative_role if safe_text(value)])
    return score


def _mode_profile(mode_id: str) -> dict[str, Any]:
    if safe_text(mode_id) == "dark_cute_breakdown":
        return dict(_DARK_CUTE_MODE_PROFILE)
    return dict(_DARK_CUTE_MODE_PROFILE)


def _artist_bias(artist_id: str) -> dict[str, Any]:
    return dict(_ARTIST_GRAMMAR_BIAS.get(safe_text(artist_id), _ARTIST_GRAMMAR_BIAS["default"]))


def _build_artist_style_prior(
    artist_id: str,
    assignments: list[dict[str, Any]],
    behavior_priors: dict[str, Any],
) -> dict[str, Any]:
    rows = [row for row in assignments if safe_text(row.get("artist_id")) == safe_text(artist_id)]
    chorus_prior = ((behavior_priors.get("sections") or {}).get("chorus") or {}) if isinstance(behavior_priors.get("sections"), dict) else {}
    return {
        "artist_id": safe_text(artist_id),
        "available": bool(rows),
        "chorus_hook_avg": _mean([float(row.get("chorus_hook_avg", 0.0) or 0.0) for row in rows]),
        "chorus_mora_avg": _mean([float(row.get("chorus_mora_avg", 0.0) or 0.0) for row in rows]),
        "dominant_form_family": _top([safe_text(row.get("form_family_id")) for row in rows]),
        "payoff_mode": _top([safe_text(row.get("payoff_mode")) for row in rows], "medium"),
        "title_return_avg": float(chorus_prior.get("preferred_title_return_count", 0) or 0),
        "artist_grammar_bias": _artist_bias(artist_id),
    }


def _build_lexical_field_bank(records: list[dict[str, Any]], mode_profile: dict[str, Any]) -> dict[str, list[str]]:
    buckets: dict[str, list[str]] = defaultdict(list)
    for record in records:
        for term in _record_terms(record):
            family = safe_text(classify_term_family(term))
            if family and term not in buckets[family]:
                buckets[family].append(term)
    for family in mode_profile.get("preferred_families", []):
        for term in mode_profile.get("fallback_terms", {}).get(family, []):
            text = _sanitize_surface_term(term)
            if text and text not in buckets[family]:
                buckets[family].append(text)
    return dict(buckets)


def _representative_mode_track_ids(artist_id: str, mode_id: str) -> list[str]:
    profile = load_representative_demo_profile(artist_id) or {}
    track_ids: list[str] = []
    mode_tracks = profile.get("mode_demo_tracks", {}) if isinstance(profile.get("mode_demo_tracks"), dict) else {}
    mode_entry = mode_tracks.get(mode_id) if isinstance(mode_tracks.get(mode_id), dict) else None
    if mode_entry:
        track_id = safe_text(mode_entry.get("track_id"))
        if track_id:
            track_ids.append(track_id)
    for item in profile.get("core_anchor_tracks", []):
        if not isinstance(item, dict):
            continue
        if safe_text(item.get("mode_id")) != safe_text(mode_id):
            continue
        track_id = safe_text(item.get("track_id"))
        if track_id and track_id not in track_ids:
            track_ids.append(track_id)
    return track_ids


def build_corpus_intelligence(
    project_root: Path,
    *,
    artist_id: str,
    mode_id: str,
    catalog_name: str = "calibration_v1",
    conditioning_records: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    form_catalog, assignments, catalog_path = _discover_form_family_assets(project_root, catalog_name=catalog_name)
    records = list(conditioning_records) if conditioning_records is not None else list(load_conditioning_records(artist_id))
    behavior_priors = load_lyric_behavior_priors(project_root, artist_ids=[artist_id], mode_id=mode_id)
    mode_profile = _mode_profile(mode_id)
    lexical_field_bank = _build_lexical_field_bank(records, mode_profile)
    representative_track_ids = _representative_mode_track_ids(artist_id, mode_id)
    proposition_signal_bank: list[dict[str, Any]] = []
    for record in records:
        track_identity = record.get("track_identity", {}) if isinstance(record.get("track_identity"), dict) else {}
        song_intent = record.get("song_intent", {}) if isinstance(record.get("song_intent"), dict) else {}
        track_id = safe_text(track_identity.get("track_id"))
        signal_score = _record_signal_score(record)
        if track_id in representative_track_ids:
            signal_score += 5
        proposition_signal_bank.append(
            {
                "track_id": track_id,
                "title_core": _record_title(record),
                "terms": _record_terms(record),
                "families": _record_family_votes(record),
                "signal_score": signal_score,
                "emotional_thesis": _sanitize_japanese_term(song_intent.get("emotional_thesis")),
                "narrative_role": [safe_text(value) for value in song_intent.get("narrative_role", []) if safe_text(value)],
                "record": record,
                "is_representative_anchor": track_id in representative_track_ids,
            }
        )
    proposition_signal_bank.sort(key=lambda item: (-int(item.get("signal_score", 0)), safe_text(item.get("track_id"))))
    return {
        "engine_type": ENGINE_TYPE,
        "artist_id": safe_text(artist_id),
        "mode_id": safe_text(mode_id),
        "catalog_path": str(catalog_path),
        "artist_style_prior": _build_artist_style_prior(artist_id, assignments, behavior_priors),
        "form_family_prior": form_catalog.get("families", {}),
        "line_behavior_bank": behavior_priors,
        "lexical_field_bank": lexical_field_bank,
        "proposition_signal_bank": proposition_signal_bank,
        "mode_profile": mode_profile,
        "representative_track_ids": representative_track_ids,
    }


def _derive_song_purpose(intent: str, intelligence: dict[str, Any]) -> str:
    if safe_text(intent):
        return safe_text(intent)
    for item in intelligence.get("proposition_signal_bank", []):
        thesis = _sanitize_japanese_term(item.get("emotional_thesis"))
        if thesis:
            return thesis
    mode_id = safe_text(intelligence.get("mode_id"))
    if mode_id == "dark_cute_breakdown":
        return "甘さの裏で圧力が壊れていく感覚を残す"
    return "聴き終わったあとに感情の残り香を残す"


def _derive_listener_position(intelligence: dict[str, Any]) -> str:
    for item in intelligence.get("proposition_signal_bank", []):
        roles = [safe_text(value).lower() for value in item.get("narrative_role", [])]
        if any("audience" in role for role in roles):
            return "audience"
        if any("other" in role or "you" in role or "direct" in role for role in roles):
            return "specific_other"
    return safe_text(intelligence.get("mode_profile", {}).get("listener_position"), "self_address")


def build_composition_brief(
    intelligence: dict[str, Any],
    *,
    intent: str = "",
    title_seed: str = "",
) -> dict[str, Any]:
    mode_profile = intelligence.get("mode_profile", {})
    seed_core = _sanitize_japanese_term(title_seed)
    if not seed_core:
        for item in intelligence.get("proposition_signal_bank", []):
            seed_core = _sanitize_japanese_term(item.get("title_core"))
            if seed_core:
                break
    if not seed_core:
        seed_core = "ひび"
    return {
        "song_purpose": _derive_song_purpose(intent, intelligence),
        "listener_position": _derive_listener_position(intelligence),
        "chorus_proposition": {
            "core_phrase": seed_core,
            "escalation_phrase": "やさしい顔では抱えきれない",
            "release_phrase": "抱えたまま落ちていく",
        },
        "singability_profile": dict(mode_profile.get("singability_profile", {})),
        "energy_curve": list(mode_profile.get("energy_curve", [])),
        "artist_grammar_bias": dict(intelligence.get("artist_style_prior", {}).get("artist_grammar_bias", {})),
        "mode_bias": {
            "mode_id": safe_text(intelligence.get("mode_id")),
            "form_family_shortlist": list(mode_profile.get("form_shortlist", [])),
            "preferred_families": list(mode_profile.get("preferred_families", [])),
        },
    }


def _normalize_core_phrase(text: Any) -> str:
    return _sanitize_japanese_term(text)


def _record_allowed_families(item: dict[str, Any], intelligence: dict[str, Any]) -> list[str]:
    families = [safe_text(value) for value in item.get("families", []) if safe_text(value)]
    if families:
        return unique_preserve_order(families)[:3]
    return list(intelligence.get("mode_profile", {}).get("preferred_families", [])[:3])


def build_proposition_archetype_set(
    intelligence: dict[str, Any],
    brief: dict[str, Any],
    *,
    title_seed: str = "",
    max_archetypes: int = 4,
) -> list[dict[str, Any]]:
    signal_bank = list(intelligence.get("proposition_signal_bank", []))
    hook_avg = float(intelligence.get("artist_style_prior", {}).get("chorus_hook_avg", 0.0) or 0.0)
    seed_core = _normalize_core_phrase(title_seed) or _normalize_core_phrase(brief.get("chorus_proposition", {}).get("core_phrase"))
    propositions: list[dict[str, Any]] = []
    used_cores: set[str] = set()

    template_count = min(max_archetypes, len(_PROPOSITION_TEMPLATES))
    for index in range(template_count):
        source = signal_bank[index % len(signal_bank)] if signal_bank else {}
        template = _PROPOSITION_TEMPLATES[index]
        core_phrase = seed_core if index == 0 and seed_core else ""
        if not core_phrase:
            core_phrase = _normalize_core_phrase(source.get("title_core"))
        if not core_phrase:
            terms = [_normalize_core_phrase(term) for term in source.get("terms", [])]
            core_phrase = next((term for term in terms if term), "")
        if not core_phrase or core_phrase in used_cores:
            continue
        used_cores.add(core_phrase)
        allowed_families = _record_allowed_families(source, intelligence)
        hook_density = safe_text(template.get("hook_density_target"))
        if hook_avg >= 2.0 and index == 0:
            hook_density = "high"
        propositions.append(
            {
                "proposition_id": f"{safe_text(intelligence.get('artist_id'))}_{safe_text(template.get('archetype_kind'))}_{index + 1}",
                "source_track_id": safe_text(source.get("track_id")),
                "source_title_core": safe_text(source.get("title_core")),
                "core_phrase": core_phrase,
                "escalation_phrase": safe_text(template.get("escalation_phrase")),
                "release_phrase": safe_text(template.get("release_phrase")),
                "allowed_lexical_families": allowed_families[:2],
                "forbidden_fragments": [core_phrase],
                "hook_density_target": hook_density,
                "title_return_policy": safe_text(template.get("title_return_policy")),
                "novelty_signature": ":".join(
                    [
                        safe_text(template.get("archetype_kind")),
                        safe_text(source.get("track_id")) or "fallback",
                        ",".join(allowed_families[:2]),
                    ]
                ),
                "archetype_kind": safe_text(template.get("archetype_kind")),
            }
        )

    if not propositions:
        fallback_core = seed_core or "ひび"
        propositions.append(
            {
                "proposition_id": f"{safe_text(intelligence.get('artist_id'))}_fallback_1",
                "source_track_id": "",
                "source_title_core": fallback_core,
                "core_phrase": fallback_core,
                "escalation_phrase": "やさしい顔では抱えきれない",
                "release_phrase": "抱えたまま落ちていく",
                "allowed_lexical_families": list(intelligence.get("mode_profile", {}).get("preferred_families", [])[:2]),
                "forbidden_fragments": [fallback_core],
                "hook_density_target": "medium",
                "title_return_policy": "anchor",
                "novelty_signature": "fallback",
                "archetype_kind": "fallback",
            }
        )

    return propositions[:max_archetypes]


def build_form_plan(intelligence: dict[str, Any], proposition: dict[str, Any]) -> dict[str, Any]:
    mode_profile = intelligence.get("mode_profile", {})
    artist_style_prior = intelligence.get("artist_style_prior", {})
    shortlist = list(mode_profile.get("form_shortlist", [])) or ["hybrid_release"]
    chorus_hook_avg = float(artist_style_prior.get("chorus_hook_avg", 0.0) or 0.0)
    chorus_mora_avg = float(artist_style_prior.get("chorus_mora_avg", 0.0) or 0.0)
    payoff_mode = safe_text(artist_style_prior.get("payoff_mode"), "medium")
    hook_compression = safe_text((artist_style_prior.get("artist_grammar_bias") or {}).get("hook_compression"))

    allow_expansive = (
        "expansive_statement" in shortlist
        and chorus_hook_avg <= 1.0
        and chorus_mora_avg >= 15.0
        and payoff_mode == "medium"
    )
    if allow_expansive:
        form_family_id = "expansive_statement"
        form_reason = "artist prior permits expansive statement cadence"
    elif chorus_hook_avg >= 2.0 or hook_compression in {"high", "very_high"}:
        form_family_id = "compressed_hook"
        form_reason = "artist prior and grammar bias favor compressed chorus-first form"
    else:
        form_family_id = "hybrid_release"
        form_reason = "proposition benefits from mixed statement-release form"

    if form_family_id not in _FORM_VARIANTS:
        form_family_id = "hybrid_release"
        form_reason = "fallback to supported rollout family"

    variant = _FORM_VARIANTS[form_family_id]
    return {
        "form_family_id": form_family_id,
        "form_family_reason": form_reason,
        "section_order": list(variant["section_order"]),
        "section_count": len(variant["section_order"]),
        "line_target_profile": list(variant["line_targets"]),
        "repetition_budget_profile": [_DEFAULT_REPETITION_BY_SECTION.get(section, 0) for section in variant["section_order"]],
        "pressure_transition_profile": [safe_text(_SECTION_ROLE_MAP.get(section)) for section in variant["section_order"]],
    }


def _section_allowed_families(section: str, proposition: dict[str, Any], intelligence: dict[str, Any]) -> list[str]:
    mode_families = list(intelligence.get("mode_profile", {}).get("preferred_families", []))
    proposition_families = list(proposition.get("allowed_lexical_families", []))
    section_specific: dict[str, list[str]] = {
        "intro": ["childhood", "architectural", "silence"],
        "verse_1": ["body", "architectural", "childhood"],
        "pre_chorus": ["mechanical", "body", "silence"],
        "chorus": proposition_families + ["collapse", "body"],
        "verse_2": proposition_families + ["body", "mechanical"],
        "pre_chorus_2": ["mechanical", "collapse", "body"],
        "bridge": ["architectural", "silence", "collapse"],
        "chorus_final": proposition_families + ["collapse", "mechanical"],
        "outro": ["silence", "architectural", "childhood"],
    }
    values = section_specific.get(section, []) + proposition_families + mode_families
    return unique_preserve_order([safe_text(value) for value in values if safe_text(value)])[:4]


def _family_terms(intelligence: dict[str, Any], families: list[str]) -> list[str]:
    lexical_field_bank = intelligence.get("lexical_field_bank", {})
    terms: list[str] = []
    for family in families:
        for term in lexical_field_bank.get(family, []):
            text = _sanitize_surface_term(term)
            if text and text not in terms:
                terms.append(text)
    return terms


def _section_scene(intelligence: dict[str, Any], section: str, families: list[str], terms: list[str]) -> str:
    preferred_scene_families = {
        "intro": ["architectural", "childhood", "silence"],
        "verse_1": ["architectural", "childhood"],
        "bridge": ["architectural", "silence"],
        "outro": ["silence", "architectural"],
    }.get(section, families)
    lexical_field_bank = intelligence.get("lexical_field_bank", {})
    for family in preferred_scene_families:
        values = lexical_field_bank.get(family, [])
        if values:
            return _sanitize_surface_term(values[0]) or safe_text(terms[0]) if terms else ""
    return safe_text(terms[0]) if terms else ""


def _section_prior(intelligence: dict[str, Any], section: str) -> dict[str, Any]:
    line_behavior = intelligence.get("line_behavior_bank", {})
    sections = line_behavior.get("sections", {}) if isinstance(line_behavior.get("sections"), dict) else {}
    prior = sections.get(section)
    return prior if isinstance(prior, dict) else {}


def build_section_behavior_plan(
    intelligence: dict[str, Any],
    brief: dict[str, Any],
    proposition: dict[str, Any],
    form_plan: dict[str, Any],
) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    section_order = list(form_plan.get("section_order", []))
    line_targets = list(form_plan.get("line_target_profile", []))
    energy_curve = list(brief.get("energy_curve", []))
    energy_stage_by_section = {
        safe_text(item.get("section")): safe_text(item.get("pressure_stage"))
        for item in energy_curve
        if isinstance(item, dict) and safe_text(item.get("section"))
    }

    for index, section in enumerate(section_order):
        prior = _section_prior(intelligence, section)
        allowed_families = _section_allowed_families(section, proposition, intelligence)
        terms = _family_terms(intelligence, allowed_families)
        default_target = int(line_targets[index]) if index < len(line_targets) else 4
        prior_range = prior.get("line_target_range")
        if isinstance(prior_range, list) and len(prior_range) == 2:
            line_target_range = [int(prior_range[0]), int(prior_range[1])]
        else:
            line_target_range = [max(2, default_target - 1), default_target]
        scene = _section_scene(intelligence, section, allowed_families, terms)
        pressure_stage = energy_stage_by_section.get(section, "set")
        title_drop_policy = _TITLE_RETURN_POLICY_BY_SECTION.get(section, "withhold")
        if section == "chorus":
            title_drop_policy = safe_text(proposition.get("title_return_policy"), "primary")
        card = {
            "section": section,
            "section_role": _SECTION_ROLE_MAP[section],
            "pressure_stage": pressure_stage,
            "semantic_carry": _SEMANTIC_CARRY_MAP[section],
            "hook_dependency": _HOOK_DEPENDENCY_MAP[section],
            "line_target_range": line_target_range,
            "line_target": default_target,
            "cadence_target": safe_text(prior.get("cadence_family"), _DEFAULT_CADENCE_BY_SECTION.get(section, "balanced")),
            "repetition_budget": int(prior.get("repetition_budget", _DEFAULT_REPETITION_BY_SECTION.get(section, 0))),
            "closure_strength_target": safe_text(prior.get("closure_strength_target"), "medium"),
            "allowed_lexical_families": allowed_families,
            "blocked_hook_fragments": list(proposition.get("forbidden_fragments", [])) if section not in {"chorus", "chorus_final"} else [],
            "title_drop_policy": title_drop_policy,
            "hook_pressure": safe_text(proposition.get("hook_density_target"), "medium"),
            "conditioning_atoms": terms[:4],
            "required_motifs": terms[:4],
            "required_imagery": terms[:3],
            "imagery_focus": terms[1:3] if len(terms) > 1 else terms[:1],
            "scene": scene,
            "narrative_goals": [
                safe_text(_SECTION_ROLE_MAP[section]),
                safe_text(_SEMANTIC_CARRY_MAP[section]),
                safe_text(brief.get("song_purpose")),
            ],
            "form_family_id": safe_text(form_plan.get("form_family_id")),
            "evidence_track_ids": [safe_text(proposition.get("source_track_id"))] if safe_text(proposition.get("source_track_id")) else [],
        }
        cards.append(card)

    return cards


def build_runtime_plan(
    intelligence: dict[str, Any],
    brief: dict[str, Any],
    proposition: dict[str, Any],
    form_plan: dict[str, Any],
    section_behavior_plan: list[dict[str, Any]],
    proposition_set: list[dict[str, Any]],
    *,
    candidate_index: int,
) -> dict[str, Any]:
    composition_brief = {
        **brief,
        "chorus_proposition": {
            "core_phrase": safe_text(proposition.get("core_phrase")),
            "escalation_phrase": safe_text(proposition.get("escalation_phrase")),
            "release_phrase": safe_text(proposition.get("release_phrase")),
        },
    }
    hook_density = safe_text(proposition.get("hook_density_target"), "medium")
    form_family_id = safe_text(form_plan.get("form_family_id"))
    return {
        "engine_type": ENGINE_TYPE,
        "track_id": f"{safe_text(intelligence.get('artist_id'))}_{safe_text(intelligence.get('mode_id'))}_{safe_text(proposition.get('proposition_id'))}_{candidate_index + 1}",
        "artist_id": safe_text(intelligence.get("artist_id")),
        "mode_id": safe_text(intelligence.get("mode_id")),
        "primary_mode": safe_text(intelligence.get("mode_id")),
        "composition_brief": composition_brief,
        "proposition_archetype_set": list(proposition_set),
        "selected_proposition": dict(proposition),
        "form_plan": dict(form_plan),
        "section_behavior_plan": list(section_behavior_plan),
        "form_family_id": form_family_id,
        "form_family_reason": safe_text(form_plan.get("form_family_reason")),
        "form_family_shortlist": list(brief.get("mode_bias", {}).get("form_family_shortlist", [])),
        "artist_grammar_bias": dict(intelligence.get("artist_style_prior", {}).get("artist_grammar_bias", {})),
        "singability_profile": dict(brief.get("singability_profile", {})),
        "hook_blueprint": {
            "core_text": safe_text(proposition.get("core_phrase")),
            "hook_density": hook_density,
            "hook_line_target": 2 if form_family_id == "compressed_hook" else 3,
            "repetition_pressure": "high" if hook_density == "high" else "medium",
        },
        "form_profile": {
            "section_order": list(form_plan.get("section_order", [])),
            "section_count": int(form_plan.get("section_count", 0) or 0),
        },
        "section_cards": list(section_behavior_plan),
    }


def _candidate_body_signatures(markdown: str, title: str = "") -> list[str]:
    signatures: list[str] = []
    title_compact = re.sub(r"\s+", "", safe_text(title))
    for raw_line in markdown.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or (line.startswith("[") and line.endswith("]")):
            continue
        compact = re.sub(r"\s+", "", line)
        if title_compact:
            compact = compact.replace(title_compact, "<TITLE>")
        if compact:
            signatures.append(compact)
    return signatures


def _surface_overlap(markdown_a: str, markdown_b: str, title_a: str = "", title_b: str = "") -> float:
    sig_a = set(_candidate_body_signatures(markdown_a, title_a))
    sig_b = set(_candidate_body_signatures(markdown_b, title_b))
    if not sig_a or not sig_b:
        return 0.0
    union = sig_a | sig_b
    if not union:
        return 0.0
    return round(len(sig_a & sig_b) / len(union), 3)


def _score_novelty(batch: list[dict[str, Any]]) -> list[dict[str, Any]]:
    proposition_counts = Counter(safe_text(item.get("proposition_id")) for item in batch if safe_text(item.get("proposition_id")))
    form_counts = Counter(safe_text(item.get("form_family_id")) for item in batch if safe_text(item.get("form_family_id")))
    scored: list[dict[str, Any]] = []
    for item in batch:
        proposition_id = safe_text(item.get("proposition_id"))
        form_family_id = safe_text(item.get("form_family_id"))
        proposition_distance = round(1.0 / max(1, proposition_counts.get(proposition_id, 1)), 3)
        form_distance = round(1.0 / max(1, form_counts.get(form_family_id, 1)), 3)
        overlaps = [
            _surface_overlap(
                safe_text(item.get("markdown")),
                safe_text(other.get("markdown")),
                safe_text(item.get("title")),
                safe_text(other.get("title")),
            )
            for other in batch
            if other is not item
        ]
        surface_overlap_penalty = max(overlaps) if overlaps else 0.0
        novelty_score = round(
            (
                proposition_distance * 0.45
                + form_distance * 0.15
                + (1.0 - surface_overlap_penalty) * 0.40
            )
            * 100.0,
            2,
        )
        enriched = dict(item)
        enriched["novelty_score"] = novelty_score
        enriched["proposition_distance"] = proposition_distance
        enriched["form_distance"] = form_distance
        enriched["surface_overlap_penalty"] = round(surface_overlap_penalty, 3)
        legacy_total = float(enriched.get("legacy_total", 0.0) or 0.0)
        musical_total = float(enriched.get("musical_total", 0.0) or 0.0)
        enriched["blended_total"] = round(
            legacy_total * 0.35 + musical_total * 0.45 + novelty_score * 0.20,
            2,
        )
        scored.append(enriched)
    return scored


def _selection_diagnostics(batch: list[dict[str, Any]], winner: dict[str, Any]) -> dict[str, Any]:
    legacy_winner = max(batch, key=lambda item: float(item.get("legacy_total", 0.0) or 0.0))
    musical_winner = max(batch, key=lambda item: float(item.get("musical_total", 0.0) or 0.0))
    novelty_winner = max(batch, key=lambda item: float(item.get("novelty_score", 0.0) or 0.0))
    blended_winner = max(batch, key=lambda item: float(item.get("blended_total", 0.0) or 0.0))
    return {
        "selection_mode": "corpus_proposition_blended_total",
        "legacy_winner": safe_text(legacy_winner.get("candidate_id")),
        "musical_winner": safe_text(musical_winner.get("candidate_id")),
        "novelty_winner": safe_text(novelty_winner.get("candidate_id")),
        "blended_winner": safe_text(blended_winner.get("candidate_id")),
        "selected_winner": safe_text(winner.get("candidate_id")),
        "winner_reason": safe_text(winner.get("winner_reason")),
        "candidates": [
            {
                "candidate_id": safe_text(item.get("candidate_id")),
                "proposition_id": safe_text(item.get("proposition_id")),
                "form_family_id": safe_text(item.get("form_family_id")),
                "legacy_total": float(item.get("legacy_total", 0.0) or 0.0),
                "musical_total": float(item.get("musical_total", 0.0) or 0.0),
                "novelty_score": float(item.get("novelty_score", 0.0) or 0.0),
                "blended_total": float(item.get("blended_total", 0.0) or 0.0),
                "surface_overlap_penalty": float(item.get("surface_overlap_penalty", 0.0) or 0.0),
            }
            for item in sorted(batch, key=lambda payload: (-float(payload.get("blended_total", 0.0) or 0.0), safe_text(payload.get("candidate_id"))))
        ],
    }


def _winner_reason(winner: dict[str, Any], diagnostics: dict[str, Any]) -> str:
    reasons: list[str] = []
    if safe_text(winner.get("candidate_id")) == safe_text(diagnostics.get("legacy_winner")):
        reasons.append("legacy_total leader")
    if safe_text(winner.get("candidate_id")) == safe_text(diagnostics.get("musical_winner")):
        reasons.append("musical_total leader")
    if float(winner.get("novelty_score", 0.0) or 0.0) >= 70.0:
        reasons.append("novelty pressure satisfied")
    if not reasons:
        reasons.append("best blended_total across proposition, form, and surface distance")
    return ", ".join(reasons)


def _promoted_critic_result(item: dict[str, Any]) -> CriticResult:
    critic_result: CriticResult = item["critic_result"]
    scores = dict(critic_result.scores)
    diagnostics = dict(critic_result.diagnostics)
    scores.update(
        {
            "total": float(item.get("blended_total", 0.0) or 0.0),
            "legacy_total": float(item.get("legacy_total", 0.0) or 0.0),
            "musical_total": float(item.get("musical_total", 0.0) or 0.0),
            "novelty_score": float(item.get("novelty_score", 0.0) or 0.0),
            "blended_total": float(item.get("blended_total", 0.0) or 0.0),
            "proposition_distance": float(item.get("proposition_distance", 0.0) or 0.0),
            "form_distance": float(item.get("form_distance", 0.0) or 0.0),
            "surface_overlap_penalty": float(item.get("surface_overlap_penalty", 0.0) or 0.0),
        }
    )
    diagnostics.update(
        {
            "novelty_score": float(item.get("novelty_score", 0.0) or 0.0),
            "proposition_distance": float(item.get("proposition_distance", 0.0) or 0.0),
            "form_distance": float(item.get("form_distance", 0.0) or 0.0),
            "surface_overlap_penalty": float(item.get("surface_overlap_penalty", 0.0) or 0.0),
        }
    )
    return replace(critic_result, scores=scores, diagnostics=diagnostics)


def _resolved_generation_mode(generation_mode: str) -> str:
    mode = safe_text(generation_mode).lower()
    if mode in {"api", "llm"}:
        return "api"
    return "template"


def run_corpus_proposition_demo(
    project_root: Path,
    *,
    artist_id: str,
    output_dir: Path,
    candidate_count: int = 4,
    mode_id: str | None = None,
    intent: str = "",
    title_seed: str = "",
    generation_mode: str = "template",
    model_provider: str = "gpt",
    model_name: str | None = None,
) -> dict[str, Any]:
    final_project_root = project_root.resolve()
    final_output_dir = output_dir.resolve()
    final_output_dir.mkdir(parents=True, exist_ok=True)

    resolved_mode_id = safe_text(mode_id) or "dark_cute_breakdown"
    resolved_candidate_count = max(2, min(int(candidate_count or 4), 4))
    resolved_generation_mode = _resolved_generation_mode(generation_mode)

    intelligence = build_corpus_intelligence(
        final_project_root,
        artist_id=artist_id,
        mode_id=resolved_mode_id,
    )
    brief = build_composition_brief(intelligence, intent=intent, title_seed=title_seed)
    proposition_set = build_proposition_archetype_set(
        intelligence,
        brief,
        title_seed=title_seed,
        max_archetypes=resolved_candidate_count,
    )

    candidate_batch: list[dict[str, Any]] = []
    prompt_packages: list[dict[str, Any]] = []
    api_generation_records: list[dict[str, Any]] = []
    for index in range(resolved_candidate_count):
        proposition = proposition_set[index % len(proposition_set)]
        form_plan = build_form_plan(intelligence, proposition)
        section_behavior_plan = build_section_behavior_plan(intelligence, brief, proposition, form_plan)
        runtime_plan = build_runtime_plan(
            intelligence,
            brief,
            proposition,
            form_plan,
            section_behavior_plan,
            proposition_set,
            candidate_index=index,
        )
        prompt_package: dict[str, Any] | None = None
        if resolved_generation_mode == "api":
            prompt_package = build_prompt_package(
                runtime_plan,
                candidate_index=index,
                model_provider=model_provider,
                model_name=model_name,
            )
            rendered = generate_candidate_via_api(
                final_project_root,
                runtime_plan,
                prompt_package,
                candidate_index=index,
                model_provider=model_provider,
                model_name=model_name,
            )
            prompt_packages.append(prompt_package)
            api_generation_records.append(
                {
                    "candidate_id": safe_text(rendered.get("candidate_id")),
                    "request_id": safe_text(prompt_package.get("request_id")),
                    "api_provider": safe_text(rendered.get("api_provider")),
                    "api_model": safe_text(rendered.get("api_model")),
                    "api_status_code": rendered.get("api_status_code"),
                    "api_finish_reason": safe_text(rendered.get("api_finish_reason")),
                    "api_error": safe_text(rendered.get("api_error")),
                    "ok": bool(rendered.get("ok")),
                }
            )
        else:
            rendered = run_renderer_stage(runtime_plan, variant_index=index, scaffold_mode=False)
        critic = run_critic_stage(runtime_plan, rendered)
        candidate_batch.append(
            {
                "candidate_id": safe_text(rendered.get("candidate_id")),
                "proposition_id": safe_text(proposition.get("proposition_id")),
                "form_family_id": safe_text(form_plan.get("form_family_id")),
                "section_order": list(form_plan.get("section_order", [])),
                "renderer_frame_family": safe_text(rendered.get("renderer_frame_family")),
                "hook_pressure_realized": safe_text(rendered.get("hook_pressure_realized")),
                "chorus_shape": safe_text(rendered.get("chorus_shape")),
                "bridge_shape": safe_text(rendered.get("bridge_shape")),
                "title": safe_text(rendered.get("title")),
                "markdown": safe_text(rendered.get("markdown")),
                "legacy_total": float(critic.scores.get("legacy_total", critic.scores.get("total", 0.0)) or 0.0),
                "musical_total": float(critic.scores.get("musical_total", 0.0) or 0.0),
                "critic_scores": dict(critic.scores),
                "critic_diagnostics": dict(critic.diagnostics),
                "critic_notes": list(critic.notes),
                "critic_result": critic,
                "runtime_plan": runtime_plan,
                "prompt_package": prompt_package,
                "generation_backend": safe_text(rendered.get("generation_backend")) or resolved_generation_mode,
                "api_provider": safe_text(rendered.get("api_provider")),
                "api_model": safe_text(rendered.get("api_model")),
                "api_status_code": rendered.get("api_status_code"),
                "api_finish_reason": safe_text(rendered.get("api_finish_reason")),
                "api_error": safe_text(rendered.get("api_error")),
            }
        )

    scored_batch = _score_novelty(candidate_batch)
    winner = max(scored_batch, key=lambda item: float(item.get("blended_total", 0.0) or 0.0))
    diagnostics = _selection_diagnostics(scored_batch, winner)
    winner["winner_reason"] = _winner_reason(winner, diagnostics)
    diagnostics["winner_reason"] = safe_text(winner.get("winner_reason"))

    promoted_critic = _promoted_critic_result(winner)
    promotion_result = run_promotion_stage(promoted_critic)
    selected_runtime_plan = winner["runtime_plan"]
    evaluation_manifest = {
        "selected_candidate_id": safe_text(winner.get("candidate_id")),
        "selected_score": float(winner.get("blended_total", 0.0) or 0.0),
        "legacy_total": float(winner.get("legacy_total", 0.0) or 0.0),
        "musical_total": float(winner.get("musical_total", 0.0) or 0.0),
        "novelty_score": float(winner.get("novelty_score", 0.0) or 0.0),
        "blended_total": float(winner.get("blended_total", 0.0) or 0.0),
        "winner_reason": safe_text(winner.get("winner_reason")),
        "proposition_distance": float(winner.get("proposition_distance", 0.0) or 0.0),
        "form_distance": float(winner.get("form_distance", 0.0) or 0.0),
        "surface_overlap_penalty": float(winner.get("surface_overlap_penalty", 0.0) or 0.0),
        "selection_diagnostics": diagnostics,
    }

    _write_json(final_output_dir / "corpus_intelligence.json", intelligence)
    _write_json(final_output_dir / "composition_brief.json", brief)
    _write_json(final_output_dir / "proposition_archetype_set.json", proposition_set)
    _write_json(final_output_dir / "runtime_plan.json", selected_runtime_plan)
    if prompt_packages:
        _write_json(final_output_dir / "prompt_packages.json", prompt_packages)
    if api_generation_records:
        _write_json(final_output_dir / "api_generation_records.json", api_generation_records)
    _write_json(
        final_output_dir / "candidate_packages.json",
        [
            {
                "candidate_id": safe_text(item.get("candidate_id")),
                "proposition_id": safe_text(item.get("proposition_id")),
                "form_family_id": safe_text(item.get("form_family_id")),
                "section_order": list(item.get("section_order", [])),
                "renderer_frame_family": safe_text(item.get("renderer_frame_family")),
                "hook_pressure_realized": safe_text(item.get("hook_pressure_realized")),
                "chorus_shape": safe_text(item.get("chorus_shape")),
                "bridge_shape": safe_text(item.get("bridge_shape")),
                "title": safe_text(item.get("title")),
                "generation_backend": safe_text(item.get("generation_backend")),
                "api_provider": safe_text(item.get("api_provider")),
                "api_model": safe_text(item.get("api_model")),
                "api_status_code": item.get("api_status_code"),
                "api_finish_reason": safe_text(item.get("api_finish_reason")),
                "api_error": safe_text(item.get("api_error")),
                "legacy_total": float(item.get("legacy_total", 0.0) or 0.0),
                "musical_total": float(item.get("musical_total", 0.0) or 0.0),
                "novelty_score": float(item.get("novelty_score", 0.0) or 0.0),
                "blended_total": float(item.get("blended_total", 0.0) or 0.0),
                "proposition_distance": float(item.get("proposition_distance", 0.0) or 0.0),
                "form_distance": float(item.get("form_distance", 0.0) or 0.0),
                "surface_overlap_penalty": float(item.get("surface_overlap_penalty", 0.0) or 0.0),
                "winner_reason": safe_text(item.get("winner_reason")),
            }
            for item in scored_batch
        ],
    )
    _write_json(final_output_dir / "evaluation_manifest.json", evaluation_manifest)
    _write_text(final_output_dir / "selected_lyric.md", safe_text(winner.get("markdown")))

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "corpus_proposition_demo_run_manifest",
        "engine_type": ENGINE_TYPE,
        "track_id": safe_text(selected_runtime_plan.get("track_id")),
        "artist_id": safe_text(artist_id),
        "mode_id": resolved_mode_id,
        "intent": safe_text(intent),
        "title_seed": safe_text(title_seed),
        "ok": bool(promoted_critic.hard_gate.passed),
        "requested_generation_mode": safe_text(generation_mode or "template"),
        "generation_mode": resolved_generation_mode,
        "model_provider": safe_text(model_provider),
        "model_name": safe_text(model_name),
        "candidate_count": resolved_candidate_count,
        "composition_brief": brief,
        "selected_proposition": dict(selected_runtime_plan.get("selected_proposition", {})),
        "form_plan": dict(selected_runtime_plan.get("form_plan", {})),
        "section_behavior_plan": list(selected_runtime_plan.get("section_behavior_plan", [])),
        "form_family_id": safe_text(winner.get("form_family_id")),
        "renderer_frame_family": safe_text(winner.get("renderer_frame_family")),
        "generation_backend": safe_text(winner.get("generation_backend")) or resolved_generation_mode,
        "api_provider": safe_text(winner.get("api_provider")),
        "api_model": safe_text(winner.get("api_model")),
        "api_status_code": winner.get("api_status_code"),
        "api_finish_reason": safe_text(winner.get("api_finish_reason")),
        "api_error": safe_text(winner.get("api_error")),
        "chorus_shape": safe_text(winner.get("chorus_shape")),
        "bridge_shape": safe_text(winner.get("bridge_shape")),
        "hook_pressure_realized": safe_text(winner.get("hook_pressure_realized")),
        "grade": safe_text(promotion_result.grade),
        "selected_candidate_id": safe_text(winner.get("candidate_id")),
        "selected_score": float(winner.get("blended_total", 0.0) or 0.0),
        "legacy_total": float(winner.get("legacy_total", 0.0) or 0.0),
        "musical_total": float(winner.get("musical_total", 0.0) or 0.0),
        "novelty_score": float(winner.get("novelty_score", 0.0) or 0.0),
        "blended_total": float(winner.get("blended_total", 0.0) or 0.0),
        "winner_reason": safe_text(winner.get("winner_reason")),
        "evaluation_manifest": evaluation_manifest,
        "selection_diagnostics": diagnostics,
        "critic": dict(promoted_critic.scores),
        "critic_diagnostics": dict(promoted_critic.diagnostics),
        "critic_notes": list(promoted_critic.notes),
        "hard_gate": {
            "passed": bool(promoted_critic.hard_gate.passed),
            "reasons": list(promoted_critic.hard_gate.reasons),
        },
        "promotion_result": {
            "candidate_id": safe_text(promotion_result.candidate_id),
            "grade": safe_text(promotion_result.grade),
            "reason": safe_text(promotion_result.reason),
        },
        "output_paths": {
            "corpus_intelligence": str((final_output_dir / "corpus_intelligence.json").resolve()),
            "composition_brief": str((final_output_dir / "composition_brief.json").resolve()),
            "proposition_archetype_set": str((final_output_dir / "proposition_archetype_set.json").resolve()),
            "runtime_plan": str((final_output_dir / "runtime_plan.json").resolve()),
            "candidate_packages": str((final_output_dir / "candidate_packages.json").resolve()),
            "evaluation_manifest": str((final_output_dir / "evaluation_manifest.json").resolve()),
            "selected_lyric": str((final_output_dir / "selected_lyric.md").resolve()),
            "prompt_packages": str((final_output_dir / "prompt_packages.json").resolve()) if prompt_packages else "",
            "api_generation_records": str((final_output_dir / "api_generation_records.json").resolve()) if api_generation_records else "",
        },
        "source_root": str(final_project_root),
        "manifest_path": str((final_output_dir / "run_manifest.json").resolve()),
        "selected_lyric_path": str((final_output_dir / "selected_lyric.md").resolve()),
    }
    _write_json(final_output_dir / "run_manifest.json", manifest)
    return manifest
