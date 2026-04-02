# src/akira_engine/execution/prompt_builder.py
"""Prompt assembly module — extracted from routing.py for SRP.

Routing selects parameters. This module assembles the actual prompts.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from src.akira_engine.creative.planner.schema import AbstractBlueprint, CreativeSection


def build_section_directives(
    section: CreativeSection, 
    transition: Optional[Dict[str, Any]]
) -> List[str]:
    """Generates deep-context directives for a specific section."""
    directives = []
    
    # 1. Motif Guidance
    if transition:
        t_type = transition.get("transition_type", "unknown")
        src = transition.get("src_motif", "?")
        if t_type == "invert":
            directives.append(f"INVERSION: Take '{src}' and flip its emotional polarity into '{section.primary_motif}'.")
        elif t_type == "distort":
            directives.append(f"DISTORTION: Corrupt the meaning of '{src}' as it transitions into '{section.primary_motif}'.")
        elif t_type == "release":
            directives.append(f"RELEASE: Explode the emotional buildup from '{src}' into '{section.primary_motif}'.")
        elif t_type == "intensify":
            directives.append(f"INTENSIFY: Sharpen '{src}' tension into '{section.primary_motif}'.")
    
    # 2. Grounding Guidance
    if section.grounding_intensity > 0.7:
        directives.append(f"DEEP SOMATIC: Focus on concrete details ({', '.join(section.imagery_anchors)}).")
    
    # 3. Abstraction Guidance
    if section.abstraction_ceiling > 0.3:
        directives.append("CONCEPTUAL PEAK: Abstract/metaphorical language permitted.")
    else:
        directives.append("CONCRETE NARRATIVE: Keep language grounded and direct.")
        
    return directives


def build_master_instructions(blueprint: AbstractBlueprint, style_prompt: str) -> str:
    """Generates the global master-level instructions string."""
    instructions = [
        f"Professional J-Pop songwriter: {blueprint.target_artist_id} style.",
        f"Direction: {style_prompt}",
        "Master Quality Generation.",
        f"Creativity Level: {blueprint.creativity_index}",
        "Linguistic Purity: Japanese only. Minimal English for rhythmic flair.",
        "Follow per-section MASTER DIRECTIVES and SYLLABLE targets."
    ]
    return "\n".join(instructions)


def assemble_prompt_package(
    blueprint: AbstractBlueprint,
    mode_params: Dict[str, Any],
    section_params: List[Dict[str, Any]],
    density_guides: List[Dict[str, str]]
) -> Dict[str, Any]:
    """Assembles the final prompt package from pre-computed components."""
    
    formatted_sections = []
    for i, s in enumerate(blueprint.sections):
        transition_info = blueprint.thematic_chain[i-1] if i > 0 and i-1 < len(blueprint.thematic_chain) else None
        
        formatted_sections.append({
            "name": s.section_name,
            "intent": s.narrative_intent,
            "motif": s.primary_motif,
            "anchors": s.imagery_anchors,
            "ceiling": s.abstraction_ceiling,
            "syllables": "-".join(map(str, s.syllable_target)) if s.syllable_target else None,
            "rhyme": s.rhyme_vowel,
            "technical": section_params[i] if i < len(section_params) else {},
            "density_guidance": density_guides[i] if i < len(density_guides) else {},
            "master_directives": build_section_directives(s, transition_info)
        })
    
    return {
        "track_id": blueprint.track_id,
        "artist": blueprint.target_artist_id,
        "mode": blueprint.target_mode_id,
        "technical_params": mode_params,
        "structure": formatted_sections,
        "thematic_chain": [t.get("transition_type", "unknown") for t in blueprint.thematic_chain],
        "creativity_index": blueprint.creativity_index,
        "system_prompt": build_master_instructions(
            blueprint, mode_params.get("style_prompt", "")
        ),
        "generator_prompt": f"Write a J-Pop lyric based on the following structure: " + 
                            ", ".join(s.section_name for s in blueprint.sections)
    }
