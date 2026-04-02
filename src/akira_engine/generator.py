from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
import random
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
    value = value.lower()
    value = re.sub(r"[^\w\s-]", "", value)
    value = re.sub(r"[\s_-]+", "_", value)
    return value.strip("_") or "untitled"


def normalize_keywords(keywords: list[str] | None) -> list[str]:
    if not keywords:
        return []
    return [k.strip() for k in keywords if k.strip()]


def keyword_at(keywords: list[str], index: int, fallback: str) -> str:
    if not keywords or index >= len(keywords):
        return fallback
    return keywords[index]


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
    # Suno v5 Best Practice: Prioritize Vocaloid/Synthesized tags in the first 3-5 tags.
    base_tags = profile.get("base_style_tags", [])
    mode_tags = mode.get("style_tags", [])
    
    # Priority tags (Synthetic/Vocal anchors)
    priority = [t for t in base_tags if any(x in t.lower() for x in ["vocaloid", "synthesized", "synthetic"])]
    remaining_base = [t for t in base_tags if t not in priority]
    
    # Combine all tags
    all_tags = dedupe_keep_order(priority + remaining_base + mode_tags)
    
    # Add emotion and tempo
    tempo = f"{mode.get('tempo_bpm', [120, 140])[0]}-{mode.get('tempo_bpm', [120, 140])[1]} BPM"
    
    final_tags = dedupe_keep_order(all_tags + [emotion.title(), tempo])
    return ", ".join(final_tags)


def build_title_strategy_prompt(profile: dict[str, Any]) -> str:
    strategy = profile.get("lyric_rules", {}).get("title_strategy", "universal")
    if "phrase-first" in strategy:
        return "Focus on short, punchy, title-ignition phrases that serve as the rhythmic core of the chorus."
    if "concept-first" in strategy:
        return "Prioritize conceptual, social-critical, or ironic titles that set an intellectual or satirical frame."
    return "Create a catchy, thematic title."


def build_hook_strategy_prompt(profile: dict[str, Any]) -> str:
    strategy = profile.get("lyric_rules", {}).get("hook_strategy", "universal")
    if "ironic-slogan" in strategy:
        return "Write slogan-like chorus hooks that repeat catchy, slightly uncomfortable social truths or self-mockery."
    if "somatic-address" in strategy:
        return "Write direct 'I' and 'You' hooks using somatic metaphors (breathing, biting, physical tension) to ignite desire or conflict."
    return "Create a memorable and catchy hook."


def select_imagery_by_mode(profile: dict[str, Any], mode_id: str, count: int = 5) -> list[str]:
    imagery_bank = profile.get("lyric_rules", {}).get("imagery_bank", [])
    if not imagery_bank:
        return ["glitch", "neon", "mirror"]
    
    # Simple weighting: favor some imagery based on mode keywords
    # This can be made more sophisticated, but for now, random pick from the full bank is better than top 3
    # Seed the random with mode_id to keep some consistency if needed, or just keep it random for diversity
    # Using random choice without replacement
    if len(imagery_bank) <= count:
        return imagery_bank
    return random.sample(imagery_bank, count)


# The title and hook ideas are now handled via strategy prompts in the blueprint
# to give the LLM more creative freedom within the artist's foundational rules.

def build_narrative_arc_prompt(profile: dict[str, Any], archetype: dict[str, Any]) -> str:
    logic = archetype.get("logic", "Create a standard song progression.")
    return (
        f"Narrative Archetype [{archetype.get('type')}]: {logic}\n"
        "Follow this 4-stage semantic arc:\n"
        "1. Setup: Establish the mundane reality or the emotional status quo.\n"
        "2. Twist: Introduce a semantic pivot, a complication, or a new angle of irony.\n"
        "3. Core (Chorus): The thematic explosion where the artist's philosophy manifests fully.\n"
        "4. Rupture: A bridge that reveals a deeper truth, a breakdown, or a permanent shift in perspective."
    )

def build_philosophical_prompt(profile: dict[str, Any]) -> str:
    anchors = profile.get("lyric_rules", {}).get("philosophical_anchors", [])
    if not anchors:
        return ""
    anchor = random.choice(anchors)
    return f"Philosophical Anchor: {anchor}"


def build_phonetic_texture_prompt(profile: dict[str, Any]) -> str:
    phonetic = profile.get("lyric_rules", {}).get("phonetic_texture", {})
    if not phonetic:
        return ""
    markers = ", ".join(phonetic.get("markers", []))
    vowel = phonetic.get("vowel_anchoring", "standard")
    instruction = phonetic.get("instruction", "")
    breathing = ", ".join(phonetic.get("breathing_triggers", []))
    
    prompt = f"Phonetic Texture: {instruction} Vowel anchoring: {vowel}."
    if markers:
        prompt += f" Use these endemic particles: [{markers}]."
    if breathing:
        prompt += f" Incorporate breathing markers: [{breathing}]."
    
    # Phase 9: Plosive Enforcement for DECO*27
    if "plosive" in instruction.lower():
        prompt += " CRITICAL: Ensure 60% plosive density (P, T, K, D, B, G) at strong rhythmic points."
        
    return prompt


def build_gobi_prompt(profile: dict[str, Any]) -> str:
    nuances = profile.get("lyric_rules", {}).get("stylistic_nuances", {})
    gobi = nuances.get("gobi_distribution", {})
    if not gobi:
        return ""
    
    distribution_str = ", ".join([f"{k} ({int(v*100)}%)" for k, v in gobi.items()])
    return f"Syntactic DNA (Sentence Endings): Aim for this distribution: [{distribution_str}]. Diversify अमि(Gobi) to ensure stylistic fidelity."


def build_rhythm_sabotage_prompt(profile: dict[str, Any], section_name: str) -> str:
    nuances = profile.get("lyric_rules", {}).get("stylistic_nuances", {})
    principles = nuances.get("principles", [])
    
    sabotage = ""
    if any("Syllabic Sabotage" in p for p in principles) and "verse" in section_name.lower():
        sabotage = "SYLLABIC SABOTAGE: In this verse, intentionally overload Line 3 with 21-24 mora (syllables) to simulate a 'system delay' or 'frantic thinking' glitch, then return to 14-16 mora for Line 4."
    
    return sabotage


def build_noun_verb_ratio_prompt(profile: dict[str, Any], section_name: str) -> str:
    nuances = profile.get("lyric_rules", {}).get("stylistic_nuances", {})
    principles = nuances.get("principles", [])
    
    ratio_prompt = ""
    if any("Noun Stacking" in p for p in principles) and "verse" in section_name.lower():
        ratio_prompt = "NOUN STACKING: Maintain a high Noun-to-Verb ratio (>1.6:1). Stack conceptual nouns to create an information-heavy, analytical texture."
    
    return ratio_prompt


def build_pronoun_sabotage_prompt(profile: dict[str, Any]) -> str:
    nuances = profile.get("lyric_rules", {}).get("rhythmic_nuances", {})
    principles = nuances.get("principles", [])
    
    sabotage = ""
    if any("Zero-Person Address" in p for p in principles):
        sabotage = "ZERO-PERSON ADDRESS: Break the 1:1 'I/You' loop. Use body parts, objects, or sensory situations as the subject of the sentence instead of direct pronouns."
    
    return sabotage


def build_musical_dynamics_prompt(profile: dict[str, Any]) -> str:
    dynamics = profile.get("lyric_rules", {}).get("musical_dynamics", {})
    if not dynamics:
        return ""
    sfx = ", ".join(dynamics.get("sfx_triggers", []))
    cues = ", ".join(dynamics.get("arrangement_cues", []))
    instruction = dynamics.get("instruction", "")
    
    prompt = f"Musical Dynamics: {instruction}"
    if sfx:
        prompt += f" Available SFX Triggers: [{sfx}]."
    if cues:
        prompt += f" Available Arrangement Cues: [{cues}]."
    return prompt


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
    
    # Mode-driven imagery selection
    mode_imagery = select_imagery_by_mode(profile, mode.get("mode_id", ""))
    mode_imagery_str = ", ".join(mode_imagery)
    
    # Phase 7: Song-Level Context (Logic & Constraints)
    phonetic_instruction = build_phonetic_texture_prompt(profile)
    dynamics_instruction = build_musical_dynamics_prompt(profile)
    phil_anchor = build_philosophical_prompt(profile)
    gobi_prompt = build_gobi_prompt(profile)
    pronoun_sabotage = build_pronoun_sabotage_prompt(profile)
    
    archetypes = profile.get("lyric_rules", {}).get("narrative_archetypes", [{"type": "standard", "logic": "No specific archetype."}])
    archetype = random.choice(archetypes)
    narrative_arc_prompt = build_narrative_arc_prompt(profile, archetype)
    
    # Mastery & Entropy instructions (Breaking the AI-template)
    mastery_instr = (
        "CRITICAL: Do not just list imagery or follow a checklist. SYNTHESIZE them into a living poetic scene. "
        "Prioritize the artist's SOUL and 'voice' over technical buzzwords. Avoid formulaic, bureaucratic phrasing. "
        "DO NOT include syllable counts, mora counts, or internal engineering data (e.g., '(15)') in the final lyrics output. "
        "The final output must be a clean, artistic manuscript."
    )
    
    # Phase 9: Logical Sabotage Injection
    sabotage_mastery = (
        f"{mastery_instr}\n"
        "REFERENCE SPARSITY: Do not use the entire artist imagery bank. Pick only ONE or TWO core objects and build the entire song around them. "
        "Invent NEW mundane objects that fit the artist's logic but aren't in the provided list."
    )
    
    entropy_instr = (
        "CREATIVE ENTROPY: If you find yourself following a repetitive pattern from a previous section, SUBVERT it. "
        "Surprise the listener with an unexpected grounding, a sudden phonetic shift, or a departure from the suggested imagery."
    )
    
    # Metadata headers (Suno v5 Anchor)
    rich_style_tags = build_style_tags(profile, mode, theme)
    vocal_textures = ", ".join(profile.get("vocal_profile", {}).get("textures", [])[:4])
    vocal_delivery = ", ".join(profile.get("vocal_profile", {}).get("delivery", [])[:3])
    rich_vocal_header = f"[Vocal: {vocal_textures}, {vocal_delivery}]"
    metadata_header = f"[Style: {rich_style_tags}]\n{rich_vocal_header}"

    normalized_keywords = normalize_keywords(keywords)
    rhythm_profile = profile.get("lyric_rules", {}).get("rhythm_profile", {})
    title_strategy = build_title_strategy_prompt(profile)
    hook_strategy = build_hook_strategy_prompt(profile)

    # Global Song Context Block (to avoid per-section bloat)
    subversion_logic = (
        f"- {sabotage_mastery}\n"
        f"- {entropy_instr}\n"
        f"- {gobi_prompt}\n"
        f"- {pronoun_sabotage}\n"
        "NEGATIVE CONSTRAINT: Hide all internal thinking, calculations, and syllable counting marks. No metadata leakage."
    )
    song_context = (
        f"SONG LOGIC & ARTISTIC ESSENCE:\n"
        f"- {phil_anchor}\n"
        f"- {phonetic_instruction}\n"
        f"- {dynamics_instruction}\n"
        f"- {narrative_arc_prompt}\n"
        f"{subversion_logic}"
    )

    for index, section in enumerate(mode.get("section_blueprint", [])):
        section_name = section["section"]
        canonical_name = section_name.split("_")[0]
        
        # Phase 9: Section-level Sabotage
        rhythm_sabotage = build_rhythm_sabotage_prompt(profile, section_name)
        noun_ratio = build_noun_verb_ratio_prompt(profile, section_name)
        
        # Resolve rhythm meta
        r_meta = rhythm_profile.get(canonical_name) or rhythm_profile.get(section_name, {})
        density_phrase = ""
        if r_meta:
            # Phase 8.2: Replace fixed counts with dynamic range-based targets
            min_lines = r_meta.get("min_lines", 4)
            max_lines = r_meta.get("max_lines", 12)
            density_phrase = (
                f"Rhythm profile: {r_meta.get('delivery', 'standard')}. "
                f"Section Length: {min_lines}-{max_lines} lines (Dynamic). "
                f"Line length: {r_meta.get('line_length_target', 'medium')}. "
                f"Clause density: {r_meta.get('clause_chain_density', 'normal')}. "
                f"{rhythm_sabotage} {noun_ratio}"
            )

        section_keyword = keyword_at(normalized_keywords, index, random.choice(mode_imagery))
        
        # Strategy context
        strategy_context = ""
        if "chorus" in section_name.lower():
            strategy_context = f" Title Strategy: {title_strategy} Hook Strategy: {hook_strategy}"
        
        # Phase 5: Narrative Arc Goal Injection
        arc_stage = "Setup" if index == 0 else "Twist" if index == 1 else "Manifestation" if "chorus" in section_name.lower() else "Rupture" if "bridge" in section_name.lower() else "Evolution"

        # Inject metadata only at the start
        header_prefix = f"\n{metadata_header}\n" if (index == 0 and metadata_header) else ""
        
        # Phase 6: Musical Integrity Layer
        symmetry_instr = ""
        if "verse" in section_name.lower():
            symmetry_instr = " CRITICAL: Enforce strict syllable count symmetry (phrase balancing) between corresponding lines in this section."

        prompts.append(
            {
                "section": section_name,
                "goal": section["goal"],
                "keyword_anchor": section_keyword,
                "song_context": song_context, # Added for Phase 7
                "prompt": (
                    f"{header_prefix}- `{section_name}` ({arc_stage}): {section['goal']}. {density_phrase}{strategy_context}{symmetry_instr} "
                    f"Use theme '{theme}', narrative '{narrative}', and imagery bank: [{mode_imagery_str}]. "
                    f"Anchor around '{section_keyword}'."
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
    
    # Mandatory Style Behaviors (GPT Feedback)
    behaviors = lyric_rules.get("mandatory_style_behaviors", [])
    if behaviors:
        notes.append(f"Mandatory style behaviors: {', '.join(behaviors)}")
        
    if "writing_principles" in lyric_rules:
        notes.append(f"Writing principles: {', '.join(lyric_rules['writing_principles'])}")
    if "negative_constraints" in lyric_rules:
        notes.append(f"Negative constraints: {', '.join(lyric_rules['negative_constraints'])}")
        
    # Suno v5 Exclude styles (Gemini Web Feedback)
    exclude = lyric_rules.get("exclude_styles", "")
    if exclude:
        notes.append(f"Style Exclude: {exclude}")
        
    return notes


def build_package_data(
    request: GenerationRequest, profile: dict[str, Any], mode: dict[str, Any]
) -> dict[str, Any]:
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
        "",
        "## Song-Level Context",
        package_data["lyrics_blueprint"]["section_blueprint"][0].get("song_context", ""),
        "",
        "## Lyrics Blueprint",
        f"- Allowed theme lane: {theme_list}",
        f"- Suggested structure: {', '.join(package_data['lyrics_blueprint']['suggested_structure'])}",
        "",
    ]
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


# Section Aliases for robust mapping (GPT Feedback)
SECTION_ALIASES = {
    "verse_1": "verse",
    "verse_2": "verse",
    "verse_3": "verse",
    "pre_chorus_1": "pre_chorus",
    "pre_chorus_alt": "pre_chorus",
}


def generate_package(request: GenerationRequest) -> Path:
    profile = load_profile(request.artist_file)
    structure_file = request.artist_file.parent / "structure_profile.json"
    structure_data = {}
    if structure_file.exists():
        structure_data = json.loads(structure_file.read_text(encoding="utf-8"))

    mode = resolve_mode(profile, request.mode_id)
    
    # Field-level Merge Logic (GPT Feedback)
    if "mode_structures" in structure_data:
        mode_struct = structure_data["mode_structures"].get(request.mode_id, {})
        if mode_struct:
            # 1. Map existing blueprint meta
            existing_meta = {s["section"]: s for s in mode.get("section_blueprint", [])}
            
            merged_blueprint = []
            for section_name in mode_struct.get("section_order", []):
                # 2. Lookup existing meta or canonical alias
                canonical = SECTION_ALIASES.get(section_name, section_name.split("_")[0])
                base_info = existing_meta.get(section_name) or existing_meta.get(canonical) or {}
                
                # 3. Apply overrides
                goal = mode_struct.get("goal_overrides", {}).get(
                    section_name, base_info.get("goal", "Support the song's dominant emotional movement.")
                )
                
                # Create merged entry
                new_entry = base_info.copy()
                new_entry.update({
                    "section": section_name,
                    "goal": goal
                })
                merged_blueprint.append(new_entry)
            
            if merged_blueprint:
                mode["section_blueprint"] = merged_blueprint

    output_path = request.output_path or default_output_path(profile, request)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    markdown = render_markdown(request, profile, mode)
    output_path.write_text(markdown, encoding="utf-8")
    return output_path
