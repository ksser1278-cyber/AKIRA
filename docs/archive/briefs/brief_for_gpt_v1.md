# [GPT BRIEF] - AKIRA ENGINE Logic & Style Review (v1.0)

Please review the following technical implementation and stylistic logic for the AKIRA ENGINE (Vocaloid/Subculture focus).

---

## 1. Context & Action
I have implemented a "High-Fidelity" style layer in [generator.py](file:///c:/JPop_Songwriter/AKIRA%20ENGINE/src/akira_engine/generator.py) to bridge the gap between static artist profiles and dynamic songwriting prompts.

- **Objective**: Ensure generated lyrics/prompts strictly follow a producer's core formula without "Human-Pop" contamination.
- **Key Fields Added**: 
    - `rhythm_density`: Controls syllable speed per section.
    - `writing_principles`: Stylistic logic rules.
    - `negative_constraints`: Hard boundaries on themes/emotions.

## 2. Review Request for GPT
Please provide a critical review of the following:

- **Logic Consistency**: Review the [generator.py](file:///c:/JPop_Songwriter/AKIRA%20ENGINE/src/akira_engine/generator.py) code (provided below). Does the fallback logic (e.g., using imagery bank as title seeds) and the structure merging from [structure_profile.json](file:///c:/JPop_Songwriter/AKIRA%20ENGINE/artists/ado/structure_profile.json) look robust?
- **Stylistic Fidelity (PinocchioP)**:
    - Are the negative constraints ("no earnest confession", "no traditional ballad arcs") sufficient to enforce his distinct cynical/meta-ironic tone?
    - Does "Rhythm density: high-density syllables" correctly trigger his signature rapid-fire delivery?
- **Stylistic Fidelity (DECO*27)**:
    - Does the "Direct Address" focus and "Somatic Metaphors" correctly capture his modern style (e.g., Rabbit Hole, Vampire)?

## 3. Reference Data

### [PinocchioP Profile Snippet]
```json
{
  "writing_principles": [
    "cute surface, toxic meaning",
    "ironic self-awareness",
    "compressed slogan hooks",
    "detached observer/cynical narrator"
  ],
  "negative_constraints": [
    "no earnest emotional confession",
    "no pure romance focus",
    "no abstract imagery without social target",
    "no traditional ballad emotional arcs",
    "avoid excessive sincerity"
  ],
  "rhythm_density": {
    "verse": "high-density syllables, rapid-fire",
    "pre_chorus": "moderate density, space for building pressure",
    "chorus": "low density per line, short and punchy repetition"
  }
}
```

### [DECO*27 Profile Snippet]
```json
{
  "writing_principles": [
    "direct address ('You' and 'I' focus)",
    "title-first hook binding",
    "somatic metaphors (biting, eating, breathing)",
    "rhythmic repetition of short words"
  ],
  "negative_constraints": [
    "no detached social commentary",
    "no third-person observational distance",
    "avoid overly complex vocabulary"
  ],
  "rhythm_density": {
    "verse": "syncopated, rhythmic, medium density",
    "chorus": "maximum hook pressure, title-driven, rhythmic chant"
  }
}
```

## 4. Full Source Code (generator.py)
```python
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REQUIRED_TOP_LEVEL_KEYS = {
    "schema_version",
    "artist_id",
    "display_name",
    "summary",
    "base_style_tags",
    "vocal_profile",
    "language_policy",
    "lyric_rules",
}


@dataclass
class GenerationRequest:
    artist_file: Path
    mode_id: str
    theme: str
    emotion: str
    narrative: str
    keywords: list[str] | None = None
    output_path: Path | None = None


def load_profile(path: Path) -> dict[str, Any]:
    profile = json.loads(path.read_text(encoding="utf-8"))
    missing = sorted(REQUIRED_TOP_LEVEL_KEYS - profile.keys())
    if missing:
        raise ValueError(f"Artist profile is missing required keys: {', '.join(missing)}")
    return profile


def resolve_mode(profile: dict[str, Any], mode_id: str) -> dict[str, Any]:
    for mode in profile["modes"]:
        if mode["mode_id"] == mode_id:
            return mode
    available = ", ".join(mode["mode_id"] for mode in profile["modes"])
    raise ValueError(f"Mode '{mode_id}' was not found. Available modes: {available}")


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return slug or "untitled"


def title_case_phrase(value: str) -> str:
    words = re.split(r"[^A-Za-z0-9]+", value)
    cleaned = [word.capitalize() for word in words if word]
    return " ".join(cleaned) or "Neon Heart"


def dedupe_keep_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    unique_items: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            unique_items.append(item)
    return unique_items


def normalize_keywords(keywords: list[str] | None) -> list[str]:
    if not keywords:
        return []
    cleaned = [keyword.strip() for keyword in keywords if keyword and keyword.strip()]
    return dedupe_keep_order(cleaned)


def keyword_at(keywords: list[str], index: int, fallback: str) -> str:
    if not keywords:
        return fallback
    return keywords[index % len(keywords)]


def build_style_tags(profile: dict[str, Any], mode: dict[str, Any], emotion: str) -> str:
    style_tags = dedupe_keep_order(
        profile.get("base_style_tags", [])
        + mode.get("style_tags", [])
        + profile.get("vocal_profile", {}).get("textures", [])
        + [emotion.title(), f"{mode.get('tempo_bpm', [120, 140])[0]}-{mode.get('tempo_bpm', [120, 140])[1]} BPM"]
    )
    return ", ".join(style_tags)


def build_title_ideas(
    profile: dict[str, Any], mode: dict[str, Any], theme: str, keywords: list[str] | None = None
) -> list[str]:
    normalized_keywords = normalize_keywords(keywords)
    theme_title = title_case_phrase(theme)
    seeds = mode.get("title_seed_words") or profile.get("lyric_rules", {}).get("imagery_bank", [])
    seed_a = seeds[0].title() if len(seeds) > 0 else "Signal"
    seed_b = seeds[1].title() if len(seeds) > 1 else "Mirror"
    seed_c = seeds[2].title() if len(seeds) > 2 else "Pulse"
    keyword_a = title_case_phrase(keyword_at(normalized_keywords, 0, "Midnight"))
    keyword_b = title_case_phrase(keyword_at(normalized_keywords, 1, "Backlight"))
    keyword_c = title_case_phrase(keyword_at(normalized_keywords, 2, "Signal"))
    keyword_d = title_case_phrase(keyword_at(normalized_keywords, 3, keyword_a))

    candidates = [
        f"{theme_title} After {keyword_b}",
        f"{seed_a} And {keyword_a}",
        f"{theme_title} / {keyword_c}",
        f"{seed_b} {keyword_d}",
        f"{seed_c} In The {keyword_a}",
    ]
    return dedupe_keep_order(candidates)


def build_hook_ideas(
    profile: dict[str, Any],
    mode: dict[str, Any],
    theme: str,
    emotion: str,
    keywords: list[str] | None = None,
) -> list[str]:
    normalized_keywords = normalize_keywords(keywords)
    imagery = profile["lyric_rules"]["imagery_bank"]
    first_image = imagery[0]
    second_image = imagery[1] if len(imagery) > 1 else imagery[0]
    theme_phrase = theme.lower().strip() or "midnight pressure"
    emotion_phrase = emotion.lower().strip() or "defiant"
    keyword_a = keyword_at(normalized_keywords, 0, first_image).lower()
    keyword_b = keyword_at(normalized_keywords, 1, second_image).lower()
    keyword_c = keyword_at(normalized_keywords, 2, "countdown").lower()
    keyword_d = keyword_at(normalized_keywords, 3, keyword_a).lower()

    hooks = [
        f"{theme_phrase}, louder than the {keyword_a} and the {first_image}",
        f"Break the {keyword_b}, let the {emotion_phrase} breathe",
        f"Count down the {keyword_d} and run straight through the {keyword_c}",
    ]
    return hooks


def build_section_prompts(profile: dict[str, Any], mode: dict[str, Any], theme: str, narrative: str) -> list[str]:
    entries = build_section_prompt_entries(profile, mode, theme, narrative)
    return [entry["prompt"] for entry in entries]


def build_section_prompt_entries(
    profile: dict[str, Any],
    mode: dict[str, Any],
    theme: str,
    narrative: str,
    keywords: list[str] | None = None,
) -> list[dict[str, str]]:
    prompts: list[dict[str, str]] = []
    imagery = ", ".join(profile.get("lyric_rules", {}).get("imagery_bank", [])[:3])
    focus = ", ".join(mode.get("lyric_focus", [])) or "narrative and imagery"
    normalized_keywords = normalize_keywords(keywords)
    rhythm_density = profile.get("lyric_rules", {}).get("rhythm_density", {})

    for index, section in enumerate(mode.get("section_blueprint", [])):
        section_name = section["section"]
        canonical_name = section_name.split("_")[0]
        density = rhythm_density.get(canonical_name) or rhythm_density.get(section_name, "")
        density_phrase = f" Rhythm density: {density}." if density else ""

        section_keyword = keyword_at(normalized_keywords, index, "signature image")
        prompts.append(
            {
                "section": section_name,
                "goal": section["goal"],
                "keyword_anchor": section_keyword,
                "prompt": (
                    f"- `{section_name}`: {section['goal']}{density_phrase} Use the theme '{theme}', "
                    f"the narrative '{narrative}', and imagery such as {imagery}. Focus on {focus}."
                    f" Anchor this section around '{section_keyword}'."
                ),
            }
        )
    return prompts


def build_generation_notes(profile: dict[str, Any], mode: dict[str, Any]) -> list[str]:
    lyric_rules = profile.get("lyric_rules", {})
    notes = [
        f"Primary language: {profile['language_policy']['primary_language']}",
        f"Avoid languages: {', '.join(profile['language_policy']['avoid_languages'])}",
        f"Vocal direction: {', '.join(profile['vocal_profile']['delivery'])}",
        f"Sonic elements: {', '.join(mode.get('sonic_elements', []))}",
        f"Avoid terms: {', '.join(lyric_rules.get('avoid_terms', []))}",
    ]
    if "writing_principles" in lyric_rules:
        notes.append(f"Writing principles: {', '.join(lyric_rules['writing_principles'])}")
    if "negative_constraints" in lyric_rules:
        notes.append(f"Negative constraints: {', '.join(lyric_rules['negative_constraints'])}")
    return notes


def build_package_data(
    request: GenerationRequest, profile: dict[str, Any], mode: dict[str, Any]
) -> dict[str, Any]:
    title_ideas = build_title_ideas(profile, mode, request.theme, request.keywords)
    hook_ideas = build_hook_ideas(
        profile, mode, request.theme, request.emotion, request.keywords
    )
    section_blueprint = build_section_prompt_entries(
        profile, mode, request.theme, request.narrative, request.keywords
    )
    generation_notes = build_generation_notes(profile, mode)
    style_tags = build_style_tags(profile, mode, request.emotion)
    return {
        "artist": {
            "artist_id": profile["artist_id"],
            "display_name": profile["display_name"],
            "summary": profile.get("summary", ""),
        },
        "input_summary": {
            "mode_id": mode.get("mode_id", "unknown"),
            "mode_label": mode.get("label", "Unknown Mode"),
            "theme": request.theme,
            "emotion": request.emotion,
            "narrative": request.narrative,
            "keywords": request.keywords or [],
        },
        "style_of_music": style_tags,
        "mode_intent": {
            "description": mode.get("description", ""),
            "tempo_range_bpm": mode.get("tempo_bpm", [120, 140]),
            "energy": mode.get("energy", "high"),
            "core_lyric_focus": mode.get("lyric_focus", []),
        },
        "title_ideas": title_ideas,
        "hook_ideas": hook_ideas,
        "lyrics_blueprint": {
            "allowed_theme_lane": profile.get("lyric_rules", {}).get("themes", []),
            "suggested_structure": profile.get("lyric_rules", {}).get("structural_defaults", []),
            "section_blueprint": section_blueprint,
        },
        "generation_notes": generation_notes,
    }


def render_markdown(request: GenerationRequest, profile: dict[str, Any], mode: dict[str, Any]) -> str:
    package_data = build_package_data(request, profile, mode)
    theme_list = ", ".join(package_data["lyrics_blueprint"]["allowed_theme_lane"])

    lines = [
        f"# {package_data['artist']['display_name']} SUNO Package",
        "",
        "## Input Summary",
        f"- Artist: {package_data['artist']['display_name']}",
        f"- Mode: {package_data['input_summary']['mode_label']} (`{package_data['input_summary']['mode_id']}`)",
        f"- Theme: {package_data['input_summary']['theme']}",
        f"- Emotion: {package_data['input_summary']['emotion']}",
        f"- Narrative: {package_data['input_summary']['narrative']}",
        "",
        "## Style of Music",
        "```",
        package_data["style_of_music"],
        "```",
        "",
        "## Mode Intent",
        f"- Description: {package_data['mode_intent']['description']}",
        f"- Tempo Range: {package_data['mode_intent']['tempo_range_bpm'][0]}-{package_data['mode_intent']['tempo_range_bpm'][1]} BPM",
        f"- Energy: {package_data['mode_intent']['energy']}",
        f"- Core Lyric Focus: {', '.join(package_data['mode_intent']['core_lyric_focus'])}",
        "",
        "## Title Ideas",
    ]

    lines.extend(f"- {title}" for title in package_data["title_ideas"])
    lines.extend(
        [
            "",
            "## Hook Ideas",
        ]
    )
    lines.extend(f"- {hook}" for hook in package_data["hook_ideas"])
    lines.extend(
        [
            "",
            "## Lyrics Blueprint",
            f"- Allowed theme lane: {theme_list}",
            f"- Suggested structure: {', '.join(package_data['lyrics_blueprint']['suggested_structure'])}",
            "",
        ]
    )
    lines.extend(
        section["prompt"] for section in package_data["lyrics_blueprint"]["section_blueprint"]
    )
    lines.extend(
        [
            "",
            "## Generation Notes",
        ]
    )
    lines.extend(f"- {note}" for note in package_data["generation_notes"])
    lines.append("")
    return "\n".join(lines)


def default_output_path(profile: dict[str, Any], request: GenerationRequest) -> Path:
    file_name = f"{profile['artist_id']}_{request.mode_id}_{slugify(request.theme)}.md"
    return Path("outputs") / file_name


def generate_package(request: GenerationRequest) -> Path:
    profile = load_profile(request.artist_file)
    structure_file = request.artist_file.parent / "structure_profile.json"
    structure_data = {}
    if structure_file.exists():
        structure_data = json.loads(structure_file.read_text(encoding="utf-8"))

    mode = resolve_mode(profile, request.mode_id)
    if "mode_structures" in structure_data:
        mode_struct = structure_data["mode_structures"].get(request.mode_id, {})
        if mode_struct:
            blueprint = []
            for section_name in mode_struct.get("section_order", []):
                goal = mode_struct.get("goal_overrides", {}).get(
                    section_name, "Support the song's dominant emotional movement."
                )
                blueprint.append({"section": section_name, "goal": goal})
            if blueprint:
                mode["section_blueprint"] = blueprint

    output_path = request.output_path or default_output_path(profile, request)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    markdown = render_markdown(request, profile, mode)
    output_path.write_text(markdown, encoding="utf-8")
    return output_path
```
