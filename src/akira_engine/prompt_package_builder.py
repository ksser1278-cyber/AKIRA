from __future__ import annotations

from typing import Any

from .lyric_utils import safe_text, unique_preserve_order


def _family_directives(form_family_id: str) -> list[str]:
    if form_family_id == "compressed_hook":
        return [
            "- compressed_hook family: chorus must feel short, percussive, and chant-like.",
            "- In [chorus], make exactly 4 lines and keep them punchy.",
            "- In [chorus], make the first two lines hook-led and start them with the core phrase.",
            "- In [chorus], do not dump motif nouns as a comma-separated list; every line must read as a natural lyric line.",
            "- In [pre_chorus] and [pre_chorus_2], keep lines short and rising; do not explain.",
            "- In [bridge], use withholding, not narrative expansion.",
            "- In [chorus_final], make exactly 6 lines, overload the hook, and make the final two lines feel irreversible.",
        ]
    if form_family_id == "hybrid_release":
        return [
            "- hybrid_release family: chorus should move statement -> hook -> release.",
            "- In [chorus], use one explanatory pressure line, one hook-led line, and one release-leaning line.",
            "- In [bridge], shift perspective or sensation instead of listing images flatly.",
            "- In [chorus_final], let the release phrase land harder than the first chorus.",
        ]
    return []


def _section_summary(card: dict[str, Any]) -> str:
    section = safe_text(card.get("section"))
    role = safe_text(card.get("section_role"))
    pressure = safe_text(card.get("pressure_stage"))
    line_target_range = card.get("line_target_range") or [int(card.get("line_target", 4) or 4)]
    allowed_families = ", ".join(safe_text(value) for value in card.get("allowed_lexical_families", []) if safe_text(value))
    blocked_fragments = ", ".join(safe_text(value) for value in card.get("blocked_hook_fragments", []) if safe_text(value))
    required_imagery = ", ".join(safe_text(value) for value in card.get("required_imagery", []) if safe_text(value))
    required_motifs = ", ".join(safe_text(value) for value in card.get("required_motifs", []) if safe_text(value))
    return "\n".join(
        [
            f"- section: {section}",
            f"  role: {role}",
            f"  pressure_stage: {pressure}",
            f"  hook_dependency: {safe_text(card.get('hook_dependency'))}",
            f"  line_target_range: {line_target_range}",
            f"  cadence_target: {safe_text(card.get('cadence_target'))}",
            f"  repetition_budget: {int(card.get('repetition_budget', 0) or 0)}",
            f"  closure_strength_target: {safe_text(card.get('closure_strength_target'))}",
            f"  scene: {safe_text(card.get('scene')) or '-'}",
            f"  required_imagery: {required_imagery or '-'}",
            f"  required_motifs: {required_motifs or '-'}",
            f"  allowed_lexical_families: {allowed_families or '-'}",
            f"  blocked_hook_fragments: {blocked_fragments or '-'}",
        ]
    )


def build_prompt_package(
    runtime_plan: dict[str, Any],
    *,
    candidate_index: int,
    model_provider: str,
    model_name: str | None,
) -> dict[str, Any]:
    composition_brief = runtime_plan.get("composition_brief", {}) if isinstance(runtime_plan.get("composition_brief"), dict) else {}
    proposition = runtime_plan.get("selected_proposition", {}) if isinstance(runtime_plan.get("selected_proposition"), dict) else {}
    form_plan = runtime_plan.get("form_plan", {}) if isinstance(runtime_plan.get("form_plan"), dict) else {}
    section_cards = list(runtime_plan.get("section_cards", []))
    hook_blueprint = runtime_plan.get("hook_blueprint", {}) if isinstance(runtime_plan.get("hook_blueprint"), dict) else {}

    required_sections = [f"[{safe_text(card.get('section'))}]" for card in section_cards if safe_text(card.get("section"))]
    section_block = "\n\n".join(_section_summary(card) for card in section_cards if isinstance(card, dict))
    exact_line_targets = {
        safe_text(card.get("section")): int(card.get("line_target", 4) or 4)
        for card in section_cards
        if isinstance(card, dict) and safe_text(card.get("section"))
    }

    core_phrase = safe_text(proposition.get("core_phrase")) or safe_text(hook_blueprint.get("core_text"))
    escalation_phrase = safe_text(proposition.get("escalation_phrase"))
    release_phrase = safe_text(proposition.get("release_phrase"))
    blocked_fragments = [
        safe_text(value)
        for card in section_cards
        for value in card.get("blocked_hook_fragments", [])
        if isinstance(card, dict) and safe_text(value)
    ]
    min_core_mentions = 4 if safe_text(proposition.get("hook_density_target")) == "high" else 3
    form_family_id = safe_text(form_plan.get("form_family_id") or runtime_plan.get("form_family_id"))
    family_directives = _family_directives(form_family_id)

    system_prompt = "\n".join(
        [
            "You are writing original Japanese lyrics from a planning package.",
            "Output only markdown lyrics.",
            "Start with a title line formatted exactly as '# <core_phrase>'.",
            "Then output the required section headers exactly once and in the required order.",
            "Do not output prose explanations, notes, JSON, or code fences.",
            "Do not invent a different title or a different main hook.",
            "Non-chorus sections must not reuse the full chorus hook or blocked hook fragments verbatim.",
            "The chorus and final chorus must realize the proposition core phrase directly and repeatedly.",
            "Keep the result singable, concrete, and section-role aware.",
        ]
    )

    user_prompt = "\n".join(
        [
            f"artist_id: {safe_text(runtime_plan.get('artist_id'))}",
            f"mode_id: {safe_text(runtime_plan.get('mode_id'))}",
            f"form_family_id: {safe_text(runtime_plan.get('form_family_id'))}",
            f"song_purpose: {safe_text(composition_brief.get('song_purpose'))}",
            f"listener_position: {safe_text(composition_brief.get('listener_position'))}",
            f"hook_core_phrase: {core_phrase}",
            f"hook_escalation_phrase: {escalation_phrase}",
            f"hook_release_phrase: {release_phrase}",
            f"hook_density_target: {safe_text(proposition.get('hook_density_target') or hook_blueprint.get('hook_density'))}",
            f"title_return_policy: {safe_text(proposition.get('title_return_policy'))}",
            f"singability_profile: {composition_brief.get('singability_profile', {})}",
            f"energy_curve: {composition_brief.get('energy_curve', [])}",
            f"artist_grammar_bias: {runtime_plan.get('artist_grammar_bias', {})}",
            "",
            "Required sections:",
            *required_sections,
            "",
            "Section behavior plan:",
            section_block,
            "",
            "Hard rules:",
            f"- Title must be exactly '{core_phrase}'.",
            f"- The exact core phrase '{core_phrase}' must appear at least {min_core_mentions} times in total.",
            f"- The exact core phrase '{core_phrase}' must appear in both [chorus] and [chorus_final].",
            f"- Use '{escalation_phrase}' as the pressure direction in [chorus].",
            f"- Use '{release_phrase}' as the release direction in [chorus_final].",
            "- For each section, actually use its scene and at least one required imagery/motif atom in natural Japanese.",
            "- Do not output comma-separated noun lists or inventory-style lines.",
            "- verse_2 must intensify pressure, not switch topic.",
            "- pre_chorus_2 must accelerate pressure, not introduce a new idea.",
            "- chorus_final is the only place allowed to sound irreversible.",
            "- keep the chorus proposition central and memorable.",
            "- Never replace the core phrase with a synonym or a different title.",
            f"- Non-chorus sections must not contain these blocked hook fragments: {', '.join(blocked_fragments) or '-'}",
            *family_directives,
            "",
            "Line count guidance by section:",
            *[f"- {section}: {count} lines" for section, count in exact_line_targets.items()],
        ]
    )

    return {
        "request_id": f"{safe_text(runtime_plan.get('track_id'))}:api:{candidate_index + 1}",
        "track_id": safe_text(runtime_plan.get("track_id")),
        "artist_id": safe_text(runtime_plan.get("artist_id")),
        "mode_id": safe_text(runtime_plan.get("mode_id")),
        "candidate_index": int(candidate_index),
        "model_provider": safe_text(model_provider),
        "model_name": safe_text(model_name),
        "proposition_id": safe_text(proposition.get("proposition_id")),
        "form_family_id": safe_text(form_plan.get("form_family_id") or runtime_plan.get("form_family_id")),
        "section_order": [safe_text(card.get("section")) for card in section_cards if safe_text(card.get("section"))],
        "output_contract": {
            "format": "markdown_section",
            "required_sections": required_sections,
            "minimum_characters": 120,
            "max_sections": len(required_sections),
            "required_title": core_phrase,
            "required_core_phrase": core_phrase,
            "required_core_sections": ["chorus", "chorus_final"],
            "min_core_phrase_mentions": min_core_mentions,
            "blocked_non_chorus_fragments": unique_preserve_order(blocked_fragments),
        },
        "system_prompt": system_prompt,
        "user_prompt": user_prompt,
        "prompt_inputs": {
            "composition_brief": composition_brief,
            "selected_proposition": proposition,
            "form_plan": form_plan,
            "section_behavior_plan": section_cards,
            "hook_blueprint": hook_blueprint,
        },
    }
