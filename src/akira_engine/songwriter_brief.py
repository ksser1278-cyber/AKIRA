from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .lyric_utils import safe_text, unique_preserve_order
from .songwriter_io import candidate_content_roots


_DARK_CUTE_SINGABILITY = {
    "hook_mora_band": [8, 12],
    "verse_mora_band": [7, 11],
    "repeatability_target": "high",
    "vowel_flow_target": "front_loaded_clear",
    "oral_friction_budget": "medium",
}

_ARTIST_GRAMMAR_BIAS = {
    "maretu": {
        "hook_compression": "high",
        "line_attack": "hard",
        "cadence_preference": ["compressed", "explosive", "rising"],
        "lexical_roughness": "high",
        "repeat_tolerance": "tight",
        "title_return_tolerance": "medium",
        "line_target_bias": "tight",
    },
    "deco27": {
        "hook_compression": "balanced",
        "line_attack": "balanced",
        "cadence_preference": ["balanced", "rising", "compressed"],
        "lexical_roughness": "medium",
        "repeat_tolerance": "medium",
        "title_return_tolerance": "medium",
        "line_target_bias": "balanced",
    },
    "pinocchiop": {
        "hook_compression": "medium_high",
        "line_attack": "pointed",
        "cadence_preference": ["compressed", "balanced", "suspended"],
        "lexical_roughness": "medium",
        "repeat_tolerance": "medium",
        "title_return_tolerance": "high",
        "line_target_bias": "balanced",
    },
    "kanaria": {
        "hook_compression": "very_high",
        "line_attack": "sharp",
        "cadence_preference": ["compressed", "rising", "explosive"],
        "lexical_roughness": "medium_high",
        "repeat_tolerance": "tight",
        "title_return_tolerance": "medium_high",
        "line_target_bias": "tightest",
    },
    "default": {
        "hook_compression": "balanced",
        "line_attack": "balanced",
        "cadence_preference": ["balanced", "compressed"],
        "lexical_roughness": "medium",
        "repeat_tolerance": "medium",
        "title_return_tolerance": "medium",
        "line_target_bias": "balanced",
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

_PRESSURE_STAGE_MAP = {
    "intro": "low",
    "verse_1": "set",
    "pre_chorus": "rising",
    "chorus": "impact",
    "verse_2": "heated",
    "pre_chorus_2": "surging",
    "bridge": "withheld",
    "chorus_final": "overload",
    "outro": "residual",
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

_CONTRAST_ROLE_MAP = {
    "intro": "setup",
    "verse_1": "pressure",
    "pre_chorus": "lift",
    "chorus": "release",
    "verse_2": "escalation",
    "pre_chorus_2": "surge",
    "bridge": "break",
    "chorus_final": "climax",
    "outro": "aftermath",
}

_BASE_FORM_VARIANTS = {
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


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            rows.append(payload)
    return rows


def _discover_form_catalog(project_root: Path, catalog_name: str) -> tuple[dict[str, Any], list[dict[str, Any]], Path]:
    search_roots = [
        Path(root).resolve()
        for root in unique_preserve_order(
            [str(project_root.resolve()), *[str(item) for item in candidate_content_roots(project_root.resolve())]]
        )
    ]
    for root in search_roots:
        catalog_path = root / "datasets" / "training" / "form_families" / catalog_name / "form_family_catalog.json"
        assignments_path = root / "datasets" / "training" / "form_families" / catalog_name / "track_form_assignments.jsonl"
        if catalog_path.exists() and assignments_path.exists():
            return _load_json(catalog_path), _load_jsonl(assignments_path), catalog_path
    raise FileNotFoundError(f"Form family catalog not found for catalog_name={catalog_name}")


def _mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return round(sum(values) / len(values), 2)


def _dominant(values: list[str], default: str = "") -> str:
    counts: dict[str, int] = {}
    for value in values:
        text = safe_text(value)
        if not text:
            continue
        counts[text] = counts.get(text, 0) + 1
    if not counts:
        return default
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))[0][0]


def _artist_form_prior(assignments: list[dict[str, Any]], artist_id: str) -> dict[str, Any]:
    rows = [row for row in assignments if safe_text(row.get("artist_id")) == safe_text(artist_id)]
    if not rows:
        return {
            "artist_id": safe_text(artist_id),
            "available": False,
            "track_count": 0,
            "chorus_hook_avg": 0.0,
            "chorus_mora_avg": 0.0,
            "payoff_mode": "",
            "dominant_form_family": "",
        }
    return {
        "artist_id": safe_text(artist_id),
        "available": True,
        "track_count": len(rows),
        "chorus_hook_avg": _mean([float(row.get("chorus_hook_avg", 0.0) or 0.0) for row in rows]),
        "chorus_mora_avg": _mean([float(row.get("chorus_mora_avg", 0.0) or 0.0) for row in rows]),
        "payoff_mode": _dominant([safe_text(row.get("payoff_mode")) for row in rows], "medium"),
        "dominant_form_family": _dominant([safe_text(row.get("form_family_id")) for row in rows]),
    }


def _dark_cute_shortlist(artist_prior: dict[str, Any]) -> list[str]:
    shortlist = ["compressed_hook", "hybrid_release"]
    if (
        float(artist_prior.get("chorus_hook_avg", 0.0) or 0.0) <= 1.0
        and float(artist_prior.get("chorus_mora_avg", 0.0) or 0.0) >= 15.0
        and safe_text(artist_prior.get("payoff_mode")) == "medium"
    ):
        shortlist.append("expansive_statement")
    return shortlist


def _select_dark_cute_family(
    artist_prior: dict[str, Any],
    shortlist: list[str],
    artist_bias: dict[str, Any],
) -> tuple[str, str]:
    if not bool(artist_prior.get("available")):
        return "hybrid_release", "artist priors sparse; defaulting to hybrid_release rollout fallback"
    chorus_hook_avg = float(artist_prior.get("chorus_hook_avg", 0.0) or 0.0)
    chorus_mora_avg = float(artist_prior.get("chorus_mora_avg", 0.0) or 0.0)
    payoff_mode = safe_text(artist_prior.get("payoff_mode"), "medium")
    compression = safe_text(artist_bias.get("hook_compression"), "balanced")
    compression_threshold = 2.0
    if compression == "very_high":
        compression_threshold = 1.45
    elif compression == "high":
        compression_threshold = 1.55
    elif compression == "medium_high":
        compression_threshold = 1.75
    if chorus_hook_avg >= compression_threshold and "compressed_hook" in shortlist:
        return "compressed_hook", "artist prior and grammar bias favor compressed hook release"
    if (
        chorus_hook_avg <= 1.0
        and chorus_mora_avg >= 15.0
        and payoff_mode == "medium"
        and "expansive_statement" in shortlist
    ):
        return "expansive_statement", "artist prior passes expansive statement gate"
    return "hybrid_release", "artist prior favors mixed release without hard hook dominance"


def _family_line_target_range(family_id: str, section_name: str, target: int) -> list[int]:
    if family_id == "compressed_hook":
        if section_name in {"pre_chorus", "pre_chorus_2", "bridge", "outro"}:
            return [max(2, target), max(3, target)]
        if section_name == "chorus_final":
            return [max(5, target - 1), target]
        return [max(3, target - 1), target]
    if section_name == "bridge":
        return [max(2, target - 1), target]
    if section_name == "chorus_final":
        return [target, target + 1]
    if section_name == "chorus":
        return [target - 1, target]
    return [target, target + 1]


def _resolve_line_target(section_name: str, base_target: int, line_target_range: list[int], artist_bias: dict[str, Any]) -> int:
    low = int(line_target_range[0]) if line_target_range else base_target
    high = int(line_target_range[-1]) if line_target_range else base_target
    bias = safe_text(artist_bias.get("line_target_bias"), "balanced")
    if section_name in {"chorus", "chorus_final"} and bias in {"tight", "tightest"}:
        return low
    if section_name.startswith("pre_chorus") and bias in {"tight", "tightest"}:
        return low
    if bias == "balanced":
        return base_target
    if bias == "tightest":
        return low
    if bias == "tight":
        return low
    return max(low, min(high, base_target))


def _cadence_target_for(section_name: str, artist_bias: dict[str, Any], family_id: str) -> str:
    preferences = [safe_text(value) for value in artist_bias.get("cadence_preference", []) if safe_text(value)]
    if section_name in {"chorus", "chorus_final"}:
        return preferences[0] if preferences else ("compressed" if family_id == "compressed_hook" else "balanced")
    if section_name.startswith("pre_chorus"):
        return preferences[1] if len(preferences) > 1 else "rising"
    if section_name == "bridge":
        return "suspended"
    return preferences[-1] if preferences else "balanced"


def _repetition_budget_for(section_name: str, artist_bias: dict[str, Any], family_id: str) -> int:
    tolerance = safe_text(artist_bias.get("repeat_tolerance"), "medium")
    if section_name == "chorus_final":
        return 2
    if section_name == "chorus":
        if family_id == "compressed_hook":
            return 2 if tolerance in {"tight", "medium"} else 1
        return 1
    if section_name.startswith("pre_chorus"):
        return 1 if tolerance in {"tight", "medium"} else 0
    return 0


def _closure_strength_for(section_name: str) -> str:
    if section_name == "chorus_final":
        return "high"
    if section_name == "chorus":
        return "medium_high"
    if section_name.startswith("pre_chorus"):
        return "medium"
    if section_name == "bridge":
        return "low"
    if section_name == "outro":
        return "medium"
    return "low"


def _family_section_specs(family_id: str, artist_bias: dict[str, Any]) -> list[dict[str, Any]]:
    variant = _BASE_FORM_VARIANTS[family_id]
    specs: list[dict[str, Any]] = []
    for section_name, base_target in zip(variant["section_order"], variant["line_targets"], strict=True):
        line_target_range = _family_line_target_range(family_id, section_name, base_target)
        line_target = _resolve_line_target(section_name, base_target, line_target_range, artist_bias)
        specs.append(
            {
                "section": section_name,
                "section_role": _SECTION_ROLE_MAP[section_name],
                "pressure_stage": _PRESSURE_STAGE_MAP[section_name],
                "hook_dependency": _HOOK_DEPENDENCY_MAP[section_name],
                "line_target_range": line_target_range,
                "line_target": line_target,
                "repetition_budget": _repetition_budget_for(section_name, artist_bias, family_id),
                "closure_strength_target": _closure_strength_for(section_name),
                "section_contrast_role": _CONTRAST_ROLE_MAP[section_name],
                "cadence_target": _cadence_target_for(section_name, artist_bias, family_id),
            }
        )
    return specs


def _core_lexical_families(catalog: dict[str, Any], family_id: str) -> list[str]:
    family = ((catalog.get("families") or {}) if isinstance(catalog.get("families"), dict) else {}).get(family_id, {})
    values = [
        safe_text(value)
        for value in family.get("dominant_lexical_families", [])
        if safe_text(value)
    ]
    return values[:2]


def build_songwriter_brief(
    project_root: Path,
    *,
    artist_id: str,
    mode_id: str,
    title_seed: str = "",
    catalog_name: str = "calibration_v1",
) -> dict[str, Any]:
    catalog, assignments, catalog_path = _discover_form_catalog(project_root.resolve(), catalog_name)
    artist_prior = _artist_form_prior(assignments, artist_id)
    artist_grammar_bias = dict(_ARTIST_GRAMMAR_BIAS.get(safe_text(artist_id), _ARTIST_GRAMMAR_BIAS["default"]))

    if safe_text(mode_id) == "dark_cute_breakdown":
        shortlist = _dark_cute_shortlist(artist_prior)
        form_family_id, form_family_reason = _select_dark_cute_family(artist_prior, shortlist, artist_grammar_bias)
        singability_profile = dict(_DARK_CUTE_SINGABILITY)
        section_specs = _family_section_specs(form_family_id if form_family_id in _BASE_FORM_VARIANTS else "hybrid_release", artist_grammar_bias)
        core_families = _core_lexical_families(catalog, form_family_id)
        composition_brief = {
            "singability_profile": singability_profile,
            "chorus_proposition": {
                "core_phrase": safe_text(title_seed),
                "escalation_phrase": "pressure escalation",
                "release_phrase": "irreversible release",
                "max_core_lexical_families": 2,
                "core_lexical_families": core_families[:2],
            },
            "hook_surface_policy": {
                "surface_mode": "hook_first",
                "core_lexical_families": core_families[:2],
                "max_core_lexical_families": 2,
                "title_return_tolerance": safe_text(artist_grammar_bias.get("title_return_tolerance"), "medium"),
                "repeatability_target": singability_profile["repeatability_target"],
            },
            "form_family_shortlist": shortlist,
            "section_energy_curve": [
                {
                    "section": spec["section"],
                    "section_role": spec["section_role"],
                    "pressure_stage": spec["pressure_stage"],
                }
                for spec in section_specs
            ],
            "mode_bias": {
                "mode_id": safe_text(mode_id),
                "rollout": "dark_cute_v1",
                "allowed_form_families": shortlist,
            },
        }
        return {
            "catalog_path": str(catalog_path),
            "artist_prior": artist_prior,
            "artist_grammar_bias": artist_grammar_bias,
            "composition_brief": composition_brief,
            "form_family_id": form_family_id,
            "form_family_reason": form_family_reason,
            "form_family_shortlist": shortlist,
            "singability_profile": singability_profile,
            "section_specs": section_specs,
        }

    fallback_specs = _family_section_specs("hybrid_release", artist_grammar_bias)
    return {
        "catalog_path": str(catalog_path),
        "artist_prior": artist_prior,
        "artist_grammar_bias": artist_grammar_bias,
        "composition_brief": {
            "singability_profile": {},
            "chorus_proposition": {
                "core_phrase": safe_text(title_seed),
                "escalation_phrase": "",
                "release_phrase": "",
                "max_core_lexical_families": 2,
                "core_lexical_families": [],
            },
            "hook_surface_policy": {
                "surface_mode": "default",
                "core_lexical_families": [],
                "max_core_lexical_families": 2,
                "title_return_tolerance": safe_text(artist_grammar_bias.get("title_return_tolerance"), "medium"),
                "repeatability_target": "medium",
            },
            "form_family_shortlist": ["hybrid_release"],
            "section_energy_curve": [
                {
                    "section": spec["section"],
                    "section_role": spec["section_role"],
                    "pressure_stage": spec["pressure_stage"],
                }
                for spec in fallback_specs
            ],
            "mode_bias": {
                "mode_id": safe_text(mode_id),
                "rollout": "fallback",
                "allowed_form_families": ["hybrid_release"],
            },
        },
        "form_family_id": "hybrid_release",
        "form_family_reason": "non-dark-cute fallback",
        "form_family_shortlist": ["hybrid_release"],
        "singability_profile": {},
        "section_specs": fallback_specs,
    }
