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


def _rhythm_contract(form_family_id: str) -> list[str]:
    lines = [
        "Rhythm-first contract:",
        "- Rhythm, cadence, and repeatability outrank semantic completeness.",
        "- If meaning detail conflicts with chantability, remove detail and keep the line attack.",
        "- Keep each lyric line singable in one breath; avoid explanatory clauses and stacked noun inventories.",
        "- Build repeated line attacks in chorus-facing sections; the first sound of a line matters.",
        "- Build rhyme flow across the whole song, not only in the chorus.",
        "- Every verse and pre-chorus should have recurring end-sounds or vowel echoes.",
        "- Use A/A/B/A or A/B/A/B tail echoes when possible; avoid four unrelated line endings in a section.",
        "- Rhyme can be subtle Japanese vowel/ending-sound echo, not forced identical words.",
        "- For every section with 3 or more lyric lines, at least 2 lines must share the same final sound.",
        "- For 4-line verses, prefer line-ending pattern A/B/A/B or A/A/B/A.",
        "- For 2-line pre-chorus sections, make both line endings feel like a tight sound pair.",
        "- For outro, keep at least one audible tail echo so the rhythm resolves.",
        "- Prefer two clean rhythmic images over four meaningful details.",
        "- Use imagery/motif atoms as light grounding only. Do not force every atom into the lyric.",
        "- Prefer compact vowel flow and clear mouth movement over dense conceptual phrasing.",
    ]
    if form_family_id == "compressed_hook":
        lines.extend(
            [
                "- compressed_hook rhythm shape for [chorus]: short / short / medium / short.",
                "- compressed_hook [chorus] lines 1 and 2 must start with the exact core phrase.",
                "- compressed_hook [chorus] hook-led lines should be clipped and chantable, not sentence-length.",
                "- compressed_hook [pre_chorus] and [pre_chorus_2] shape: short / short lift, no explanation.",
                "- compressed_hook verses should use tight end-sound echoes so the rhythm is already moving before the hook.",
                "- compressed_hook [chorus_final] shape: hook / hook / break / hook / release / release.",
            ]
        )
    elif form_family_id == "hybrid_release":
        lines.extend(
            [
                "- hybrid_release rhythm shape for [chorus]: medium statement / short hook / pressure / short hook / release.",
                "- hybrid_release [chorus] hook lines should be repeatable as crowd-call fragments.",
                "- hybrid_release [pre_chorus] shape: medium / medium / lifted pressure.",
                "- hybrid_release verses should use smooth A/B/A/B tail echoes, then tighten in pre_chorus.",
                "- hybrid_release [bridge] shape: delayed viewpoint / sensory turn / breath before release.",
                "- hybrid_release [chorus_final] must repeat the hook attack but land the release harder.",
            ]
        )
    return lines


def _section_summary(card: dict[str, Any]) -> str:
    section = safe_text(card.get("section"))
    role = safe_text(card.get("section_role"))
    pressure = safe_text(card.get("pressure_stage"))
    line_target_range = card.get("line_target_range") or [int(card.get("line_target", 4) or 4)]
    allowed_families = ", ".join(safe_text(value) for value in card.get("allowed_lexical_families", []) if safe_text(value))
    blocked_fragments = ", ".join(safe_text(value) for value in card.get("blocked_hook_fragments", []) if safe_text(value))
    required_imagery = ", ".join(safe_text(value) for value in card.get("required_imagery", []) if safe_text(value))
    required_motifs = ", ".join(safe_text(value) for value in card.get("required_motifs", []) if safe_text(value))
    tail_pattern = "/".join(safe_text(value) for value in card.get("tail_sound_pattern", []) if safe_text(value))
    tail_pool = ", ".join(safe_text(value) for value in card.get("target_tail_pool", []) if safe_text(value))
    internal_slots = ", ".join(str(value) for value in card.get("internal_rhyme_slots", []))
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
            f"  tail_sound_pattern: {tail_pattern or '-'}",
            f"  target_tail_pool_sound_only: {tail_pool or '-'}",
            f"  internal_rhyme_slots: {internal_slots or '-'}",
            f"  rhyme_density_target: {safe_text(card.get('rhyme_density_target')) or '-'}",
            f"  rhyme_role: {safe_text(card.get('rhyme_role')) or '-'}",
        ]
    )


def _rhyme_plan_summary(rhyme_plan: dict[str, Any]) -> str:
    if not rhyme_plan:
        return "-"
    lines = [
        f"plan_id: {safe_text(rhyme_plan.get('plan_id'))}",
        f"priority: {safe_text(rhyme_plan.get('priority'))}",
        f"tail_sound_pool: {', '.join(safe_text(value) for value in rhyme_plan.get('tail_sound_pool', []) if safe_text(value)) or '-'}",
    ]
    for spec in rhyme_plan.get("section_rhyme_specs", []):
        if not isinstance(spec, dict):
            continue
        pattern = "/".join(safe_text(value) for value in spec.get("tail_sound_pattern", []) if safe_text(value))
        pool = ", ".join(safe_text(value) for value in spec.get("target_tail_pool", []) if safe_text(value))
        slots = ", ".join(str(value) for value in spec.get("internal_rhyme_slots", []))
        lines.append(
            f"- {safe_text(spec.get('section'))}: pattern={pattern or '-'}; tail_sounds={pool or '-'}; internal_slots={slots or '-'}; density={safe_text(spec.get('rhyme_density_target'))}; role={safe_text(spec.get('rhyme_role'))}"
        )
    return "\n".join(lines)


def _vocal_material_plan_summary(vocal_material_plan: dict[str, Any]) -> str:
    if not vocal_material_plan:
        return "-"
    identity = vocal_material_plan.get("songwriter_identity_contract", {})
    role = safe_text(identity.get("role")) if isinstance(identity, dict) else ""
    priority = ", ".join(
        safe_text(value)
        for value in vocal_material_plan.get("priority_order", [])
        if safe_text(value)
    )
    hook_shape = vocal_material_plan.get("hook_phoneme_shape", {})
    lines = [
        f"songwriter_role: {role or '-'}",
        f"priority_order: {priority or '-'}",
        f"hook_phoneme_shape: {hook_shape if isinstance(hook_shape, dict) else {}}",
        "learning_sources:",
    ]
    for source in vocal_material_plan.get("learning_source_contract", []):
        if not isinstance(source, dict):
            continue
        lines.append(
            f"- {safe_text(source.get('source'))}: learns={safe_text(source.get('learns'))}; used_for={safe_text(source.get('used_for'))}"
        )
    lines.append("line_realization:")
    terminal_bank = vocal_material_plan.get("terminal_word_bank", {})
    if isinstance(terminal_bank, dict):
        lines.append(f"terminal_word_bank: {terminal_bank}")
    for plan in vocal_material_plan.get("line_realization_plan", []):
        if not isinstance(plan, dict):
            continue
        patterns = " | ".join(safe_text(value) for value in plan.get("syntax_patterns", []) if safe_text(value))
        terminals = ", ".join(safe_text(value) for value in plan.get("terminal_word_candidates", [])[:8] if safe_text(value))
        avoid = ", ".join(safe_text(value) for value in plan.get("avoid", []) if safe_text(value))
        line_end_parts: list[str] = []
        for target in plan.get("line_end_grid", []):
            if not isinstance(target, dict):
                continue
            words = "/".join(
                safe_text(value)
                for value in target.get("allowed_terminal_words", [])[:4]
                if safe_text(value)
            )
            line_end_parts.append(
                f"L{int(target.get('line_index', 0) or 0)}={safe_text(target.get('pattern_label'))}:{safe_text(target.get('tail_sound'))}[{words or '-'}]"
            )
        lines.append(
            f"- {safe_text(plan.get('section'))}: pressure={safe_text(plan.get('pressure_stage'))}; patterns={patterns or '-'}; terminal_words={terminals or '-'}; line_end_grid={'; '.join(line_end_parts) or '-'}; avoid={avoid or '-'}"
        )
    lines.append("rhythm_cells:")
    for plan in vocal_material_plan.get("rhythm_cell_plan", []):
        if not isinstance(plan, dict):
            continue
        cells = " | ".join(safe_text(value) for value in plan.get("rhythm_cells", []) if safe_text(value))
        lines.append(
            f"- {safe_text(plan.get('section'))}: line_attack={safe_text(plan.get('line_attack_mode'))}; breath_cut={safe_text(plan.get('breath_cut'))}; cells={cells or '-'}"
        )
    return "\n".join(lines)


def _required_line_endings_summary(vocal_material_plan: dict[str, Any]) -> str:
    section_grid = vocal_material_plan.get("section_line_end_grid", {})
    if not isinstance(section_grid, dict) or not section_grid:
        return "-"
    lines: list[str] = []
    for section, grid in section_grid.items():
        if not isinstance(grid, list):
            continue
        parts: list[str] = []
        for target in grid:
            if not isinstance(target, dict) or target.get("required_for_validation") is False:
                continue
            words = [
                safe_text(value)
                for value in target.get("allowed_terminal_words", [])[:4]
                if safe_text(value)
            ]
            if not words:
                continue
            parts.append(
                f"L{int(target.get('line_index', 0) or 0)} must end with {safe_text(target.get('tail_sound'))}: "
                + "/".join(words)
            )
        if parts:
            lines.append(f"- [{safe_text(section)}]: " + "; ".join(parts))
    return "\n".join(lines) if lines else "-"


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
    rhyme_plan = runtime_plan.get("rhyme_plan", {}) if isinstance(runtime_plan.get("rhyme_plan"), dict) else {}
    songwriter_identity_contract = (
        runtime_plan.get("songwriter_identity_contract", {})
        if isinstance(runtime_plan.get("songwriter_identity_contract"), dict)
        else {}
    )
    vocal_material_plan = (
        runtime_plan.get("vocal_material_plan", {})
        if isinstance(runtime_plan.get("vocal_material_plan"), dict)
        else {}
    )

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
    theme_lane = composition_brief.get("theme_lane", {}) if isinstance(composition_brief.get("theme_lane"), dict) else {}
    forbidden_theme_motifs = [
        safe_text(value)
        for value in theme_lane.get("forbidden_motifs", [])
        if safe_text(value)
    ]

    system_prompt = "\n".join(
        [
            "You are an utaite/vocaloid singer-songwriter writing original Japanese lyrics from a planning package.",
            "Role ID: utaite_vocaloid_singer_songwriter.",
            "Treat every lyric line as vocal material for melody, breath, rhyme, and mouthfeel.",
            "Output only markdown lyrics.",
            "Start with a title line formatted exactly as '# <core_phrase>'.",
            "Then output the required section headers exactly once and in the required order.",
            "Do not output prose explanations, notes, JSON, or code fences.",
            "Do not invent a different title or a different main hook.",
            "Non-chorus sections must not reuse the full chorus hook or blocked hook fragments verbatim.",
            "The chorus and final chorus must realize the proposition core phrase directly and repeatedly.",
            "Keep the result rhythm-first, singable, concrete, and section-role aware.",
            "Cadence and mouth-feel outrank semantic completeness.",
            "Do not write poetry-first explanations, motif inventories, or theme summaries.",
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
            f"songwriter_identity_contract: {songwriter_identity_contract}",
            f"theme_lane: {theme_lane}",
            "",
            "Required sections:",
            *required_sections,
            "",
            "Section behavior plan:",
            section_block,
            "",
            "Rhyme plan:",
            _rhyme_plan_summary(rhyme_plan),
            "",
            "Vocal material plan:",
            _vocal_material_plan_summary(vocal_material_plan),
            "",
            "Required line endings:",
            _required_line_endings_summary(vocal_material_plan),
            "",
            "Hard rules:",
            f"- Title must be exactly '{core_phrase}'.",
            f"- The exact core phrase '{core_phrase}' must appear at least {min_core_mentions} times in total.",
            f"- The exact core phrase '{core_phrase}' must appear in both [chorus] and [chorus_final].",
            f"- Use '{escalation_phrase}' as the pressure direction in [chorus].",
            f"- Use '{release_phrase}' as the release direction in [chorus_final].",
            "- Use each section scene as light grounding; if imagery detail damages rhythm, keep only one strong atom.",
            "- Do not output comma-separated noun lists or inventory-style lines.",
            "- verse_2 must intensify pressure, not switch topic.",
            "- pre_chorus_2 must accelerate pressure, not introduce a new idea.",
            "- chorus_final is the only place allowed to sound irreversible.",
            "- keep the chorus proposition central and memorable.",
            "- Never replace the core phrase with a synonym or a different title.",
            f"- Do not use these overused theme motifs anywhere: {', '.join(forbidden_theme_motifs) or '-'}",
            "- Build the setting from the current theme_lane instead of candy/toy/room imagery.",
            "- Obey each section's tail_sound_pattern from the Rhyme plan. Same letters must share an audible final sound.",
            "- Use target_tail_pool as sound targets, not as mandatory literal words.",
            "- Use vocal_material_plan.terminal_word_bank for natural line endings that satisfy those sounds.",
            "- For each section, obey vocal_material_plan.section_line_end_grid line by line.",
            "- Lines listed in Required line endings are validation anchors; their final written characters must be one listed terminal word.",
            "- Do not add particles, punctuation words, or extra clauses after a required terminal word.",
            "- If line_end_grid says L1=A:る, line 1 must end with a natural る-word candidate such as 残る, 鳴る, 揺れる, 崩れる, 刺さる, or 染みる.",
            "- Same pattern label must use the same tail sound family inside that section. A/A/B/A means lines 1, 2, and 4 need the same final sound family.",
            "- Every lyric line must realize one rhythm cell and one breath cut from the vocal material plan.",
            "- Do not explain the theme. Write sung attacks, tail echoes, and short repeatable phrases.",
            "- Never end a line with an isolated tail marker such as る, く, い, て, う, む, ん, or ない.",
            "- Bad endings: 'まだ る', '少し く', '温度 い'. Use natural Japanese words that already carry the sound.",
            "- Good endings for る/く/い/て: 残る, 鳴る, 深く, 遠く, 痛い, 近い, ほどけて.",
            f"- Non-chorus sections must not contain these blocked hook fragments: {', '.join(blocked_fragments) or '-'}",
            *family_directives,
            "",
            *_rhythm_contract(form_family_id),
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
            "forbidden_theme_motifs": unique_preserve_order(forbidden_theme_motifs),
            "rhythm_first": True,
            "whole_song_rhyme_required": True,
            "rhyme_plan": rhyme_plan,
            "songwriter_identity_contract": songwriter_identity_contract,
            "vocal_material_plan": vocal_material_plan,
            "minimum_line_end_alignment": float(vocal_material_plan.get("minimum_line_end_alignment", 0.55) or 0.55),
            "rhythm_priority": [
                "line_attack",
                "whole_song_rhyme_flow",
                "end_sound_echo",
                "repeatability",
                "prosodic_flow",
                "vowel_flow",
                "hook_cadence_payoff",
            ],
        },
        "system_prompt": system_prompt,
        "user_prompt": user_prompt,
        "prompt_inputs": {
            "composition_brief": composition_brief,
            "theme_lane": theme_lane,
            "selected_proposition": proposition,
            "form_plan": form_plan,
            "section_behavior_plan": section_cards,
            "rhyme_plan": rhyme_plan,
            "songwriter_identity_contract": songwriter_identity_contract,
            "vocal_material_plan": vocal_material_plan,
            "hook_blueprint": hook_blueprint,
        },
    }
