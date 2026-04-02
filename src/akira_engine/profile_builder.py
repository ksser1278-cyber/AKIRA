from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


LANGUAGE_MAP = {
    "ja": "Japanese",
    "en": "English",
    "ko": "Korean",
}

MODE_TEMPLATES = {
    "rebellious_dark": {
        "label": "Rebellious Dark",
        "description": "Corpus-derived lane centered on fracture imagery, dark contrasts, and high-tension chorus release.",
        "tempo_bpm": [145, 160],
        "energy": "high",
        "style_tags": ["J-Rock", "Dark Edge", "Hook-Centered", "High Tension"],
        "sonic_elements": ["distorted lift", "driving rhythm", "sharp chorus release"],
        "lyric_focus": ["defiance", "fracture imagery", "voice against pressure"],
    },
    "night_drive": {
        "label": "Night Drive",
        "description": "Corpus-derived lane built on city-night motion, neon imagery, and forward momentum.",
        "tempo_bpm": [124, 132],
        "energy": "medium_high",
        "style_tags": ["J-Pop", "Urban Night", "Motion", "Hook-Centered"],
        "sonic_elements": ["steady pulse", "night-city atmosphere", "forward-moving groove"],
        "lyric_focus": ["night escape", "urban movement", "restless momentum"],
    },
    "anthemic_cinematic": {
        "label": "Anthemic Cinematic",
        "description": "Corpus-derived lane that leans on light-dark contrast and a build toward final release.",
        "tempo_bpm": [126, 138],
        "energy": "medium_high",
        "style_tags": ["Anthemic", "Cinematic Rise", "Light-Dark Contrast", "Final Release"],
        "sonic_elements": ["wide lift", "cinematic swell", "final-release chorus"],
        "lyric_focus": ["breakthrough", "arrival", "uplift after tension"],
    },
    "intimate_confessional": {
        "label": "Intimate Confessional",
        "description": "Corpus-derived lane focused on first-person voice, body imagery, and inward emotional detail.",
        "tempo_bpm": [78, 98],
        "energy": "medium_low",
        "style_tags": ["Confessional", "First-Person", "Body Imagery", "Inner Tension"],
        "sonic_elements": ["close vocal focus", "restrained dynamics", "emotional pullback"],
        "lyric_focus": ["self-address", "vulnerability", "private pressure"],
    },
}

FUNCTION_GOALS = {
    "atmosphere": "Open with atmosphere and signal the image world immediately.",
    "scene_setting": "Establish a vivid visual frame before the main emotional push.",
    "narrative_detail": "Carry concrete details and perspective-specific storytelling.",
    "detail_build": "Increase specificity and tension through denser descriptive lines.",
    "escalation": "Compress the language and tighten emotion before the chorus release.",
    "hook_release": "Deliver the core hook in a chantable, memorable form.",
    "declaration": "State the song's main emotional claim clearly and directly.",
    "chantable_hook": "Keep the line shape short enough to repeat and sing back easily.",
    "perspective_shift": "Change angle or emotional framing before the final section.",
    "vulnerability_drop": "Momentarily expose a softer or more fragile emotional layer.",
    "fade_or_afterimage": "Leave a final emotional afterimage rather than a new plot beat.",
}

FALLBACK_SECTION_BLUEPRINT = [
    ("verse_1", "narrative_detail"),
    ("pre_chorus", "escalation"),
    ("chorus", "hook_release"),
    ("verse_2", "detail_build"),
    ("chorus", "declaration"),
    ("bridge", "perspective_shift"),
    ("chorus_final", "hook_release"),
]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return slug or "unknown"


def dedupe_keep_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            result.append(item)
    return result


def language_name(code: str) -> str:
    return LANGUAGE_MAP.get(code.lower(), code.upper())


def take_terms(items: list[dict[str, Any]], key: str, limit: int) -> list[str]:
    return [item[key] for item in items[:limit] if item.get(key)]


def is_unlabeled_label(label: str) -> bool:
    return label.startswith("unlabeled") or label == "untitled"


def has_meaningful_structure(analysis: dict[str, Any]) -> bool:
    common_structures = analysis["structural_profile"].get("common_structures", [])
    if not common_structures:
        return False
    top_pattern = common_structures[0]["pattern"]
    labels = [part.strip() for part in top_pattern.split("->")]
    return any(not is_unlabeled_label(label) for label in labels)


def build_summary(analysis: dict[str, Any]) -> str:
    imagery = take_terms(analysis["imagery_profile"]["top_imagery_clusters"], "tag", 3)
    arcs = take_terms(analysis["emotional_profile"]["dominant_arc_patterns"], "arc", 1)
    hooks = analysis["hook_pattern_summary"]["common_hook_sections"]
    hook_section = hooks[0]["section"] if hooks else "chorus"
    hook_phrase = "stanza-centered hook writing" if is_unlabeled_label(hook_section) else f"{hook_section}-centered hook writing"
    imagery_phrase = ", ".join(imagery) if imagery else "strong recurring imagery"
    arc_phrase = arcs[0].replace("_", " ") if arcs else "section-to-section contrast"
    return (
        f"Lyrics-derived draft profile emphasizing {imagery_phrase}, "
        f"{hook_phrase}, and a {arc_phrase} emotional shape."
    )


def build_base_style_tags(analysis: dict[str, Any]) -> list[str]:
    imagery = take_terms(analysis["imagery_profile"]["top_imagery_clusters"], "tag", 4)
    dominant_perspective = analysis["vocabulary_profile"]["pronoun_profile"]["dominant_perspective"]
    tags = ["J-Pop", "Lyrics-Derived Draft", "Hook-Centered"]
    if dominant_perspective == "first_person":
        tags.append("First-Person Voice")
    if "night" in imagery:
        tags.append("Night Imagery")
    if "city" in imagery:
        tags.append("Urban Imagery")
    if "fracture" in imagery:
        tags.append("Dark Contrast")
    if "body" in imagery:
        tags.append("Body Imagery")
    return dedupe_keep_order(tags)


def build_vocal_profile(analysis: dict[str, Any]) -> dict[str, Any]:
    hook_sections = take_terms(analysis["hook_pattern_summary"]["common_hook_sections"], "section", 3)
    arc = take_terms(analysis["emotional_profile"]["dominant_arc_patterns"], "arc", 1)
    if hook_sections and any(not is_unlabeled_label(section) for section in hook_sections):
        hook_zone = ", ".join(hook_sections)
    else:
        hook_zone = "repeated stanza clusters"
    return {
        "range_hint": (
            "Lyrics-only draft: prioritize section contrast and hook lift. "
            f"Most active hook zones appear in {hook_zone}."
        ),
        "textures": [
            "hook-forward phrasing",
            "image-dense lines",
            "section-contrast writing",
        ],
        "delivery": [
            "clear section escalation",
            arc[0].replace("_", " ") if arc else "chorus lift",
            "first-person emotional framing",
        ],
    }


def build_language_policy(analysis: dict[str, Any]) -> dict[str, Any]:
    primary = language_name(analysis.get("language", "ja"))
    english_ratio = analysis["vocabulary_profile"]["average_english_insertion_ratio"]
    avoid: list[str] = []
    if english_ratio < 0.35:
        avoid.append("English-heavy lyrics")
    return {
        "primary_language": primary,
        "allowed_languages": [primary],
        "avoid_languages": avoid,
    }


def derive_themes(analysis: dict[str, Any]) -> list[str]:
    themes: list[str] = []
    for mode in analysis["mode_candidates"][:3]:
        if mode["mode"] == "rebellious_dark":
            themes.extend(["defiance under pressure", "fracture and resistance"])
        elif mode["mode"] == "night_drive":
            themes.extend(["night movement", "urban restlessness"])
        elif mode["mode"] == "anthemic_cinematic":
            themes.extend(["breakthrough after darkness", "arrival and release"])
        elif mode["mode"] == "intimate_confessional":
            themes.extend(["private tension", "confessional self-address"])
    arc = take_terms(analysis["emotional_profile"]["dominant_arc_patterns"], "arc", 1)
    if arc:
        themes.append(arc[0].replace("_", " "))
    return dedupe_keep_order(themes)[:6]


def build_lyric_rules(analysis: dict[str, Any]) -> dict[str, Any]:
    imagery_bank = take_terms(analysis["imagery_profile"]["top_imagery_terms"], "term", 8)
    if has_meaningful_structure(analysis):
        structure_pattern = analysis["structural_profile"]["common_structures"][0]["pattern"]
        structural_defaults = [part.strip() for part in structure_pattern.split("->")]
    else:
        structural_defaults = [item[0] for item in FALLBACK_SECTION_BLUEPRINT]
    return {
        "themes": derive_themes(analysis),
        "imagery_bank": imagery_bank,
        "avoid_terms": ["direct artist naming", "unreviewed audio assumptions"],
        "structural_defaults": structural_defaults,
    }


def build_section_blueprint(analysis: dict[str, Any]) -> list[dict[str, str]]:
    if not has_meaningful_structure(analysis):
        blueprint: list[dict[str, str]] = []
        for section_name, function_name in FALLBACK_SECTION_BLUEPRINT:
            goal = FUNCTION_GOALS.get(function_name, "Support the song's dominant emotional movement.")
            if section_name == "chorus_final":
                goal = f"{goal} Push the final chorus as the clearest emotional release point."
            blueprint.append({"section": section_name, "goal": goal})
        return blueprint

    defaults_by_section = {
        section["section"]: section for section in analysis["section_role_defaults"]
        if not is_unlabeled_label(section["section"])
    }
    structure_pattern = analysis["structural_profile"]["common_structures"][0]["pattern"]
    ordered_sections = [part.strip() for part in structure_pattern.split("->")]
    blueprint: list[dict[str, str]] = []
    seen: set[str] = set()

    for ordered_label in ordered_sections:
        canonical = "pre_chorus" if ordered_label.startswith("pre_chorus") else ordered_label.split("_")[0]
        if canonical in seen or canonical not in defaults_by_section:
            continue
        seen.add(canonical)
        section = defaults_by_section[canonical]
        functions = [item["function"] for item in section["common_functions"]]
        emotions = [item["emotion"] for item in section["common_emotions"]]
        goal_parts = [FUNCTION_GOALS[name] for name in functions if name in FUNCTION_GOALS]
        if emotions:
            goal_parts.append(f"Lean into a {emotions[0].replace('_', ' ')} emotional color.")
        goal = " ".join(goal_parts) if goal_parts else "Support the song's dominant emotional movement."
        blueprint.append({"section": ordered_label, "goal": goal})
    return blueprint


def build_title_seed_words(analysis: dict[str, Any]) -> list[str]:
    imagery_terms = take_terms(analysis["imagery_profile"]["top_imagery_terms"], "term", 5)
    token_terms = take_terms(analysis["vocabulary_profile"]["top_tokens"], "token", 5)
    return dedupe_keep_order(imagery_terms + token_terms)[:8]


def build_mode(mode_name: str, analysis: dict[str, Any], section_blueprint: list[dict[str, str]]) -> dict[str, Any]:
    template = MODE_TEMPLATES[mode_name]
    imagery = take_terms(analysis["imagery_profile"]["top_imagery_clusters"], "tag", 3)
    focus = dedupe_keep_order(template["lyric_focus"] + [item.replace("_", " ") for item in imagery])[:5]
    title_seeds = build_title_seed_words(analysis)
    return {
        "mode_id": slugify(mode_name),
        "label": template["label"],
        "description": template["description"],
        "tempo_bpm": template["tempo_bpm"],
        "energy": template["energy"],
        "style_tags": dedupe_keep_order(template["style_tags"] + build_base_style_tags(analysis))[:8],
        "sonic_elements": template["sonic_elements"],
        "lyric_focus": focus,
        "title_seed_words": title_seeds,
        "section_blueprint": section_blueprint,
    }


def default_output_path(analysis: dict[str, Any]) -> Path:
    return Path("artists") / analysis["artist_id"] / "profile.generated.json"


def build_profile_from_analysis(analysis: dict[str, Any]) -> dict[str, Any]:
    section_blueprint = build_section_blueprint(analysis)
    selected_modes = [item["mode"] for item in analysis["mode_candidates"][:4] if item["mode"] in MODE_TEMPLATES]
    if not selected_modes:
        selected_modes = ["anthemic_cinematic"]

    return {
        "schema_version": "1.0",
        "artist_id": analysis["artist_id"],
        "display_name": analysis["artist_name"],
        "summary": build_summary(analysis),
        "reference_notes": [
            "Auto-derived from lyric analysis evidence, not from direct audio modeling.",
            "Treat vocal and sonic fields as draft heuristics that require human review.",
        ],
        "base_style_tags": build_base_style_tags(analysis),
        "vocal_profile": build_vocal_profile(analysis),
        "language_policy": build_language_policy(analysis),
        "lyric_rules": build_lyric_rules(analysis),
        "modes": [build_mode(mode_name, analysis, section_blueprint) for mode_name in selected_modes],
    }


def derive_profile(analysis_path: Path, output_path: Path | None = None) -> Path:
    analysis = load_json(analysis_path)
    profile = build_profile_from_analysis(analysis)
    final_path = output_path or default_output_path(analysis)
    final_path.parent.mkdir(parents=True, exist_ok=True)
    final_path.write_text(json.dumps(profile, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return final_path
