from __future__ import annotations

from typing import Any

from .lyric_utils import safe_text, unique_preserve_order


SONGWRITER_IDENTITY_CONTRACT: dict[str, Any] = {
    "role": "utaite_vocaloid_singer_songwriter",
    "primary_output": "vocal_material",
    "line_rule": "write singable vocal gestures, not explanatory lyric prose",
    "priority_order": [
        "mouthfeel",
        "rhythm_cell",
        "tail_sound_echo",
        "repeatability",
        "hook_phoneme_shape",
        "section_energy",
        "minimal_image",
        "meaning",
    ],
    "forbidden_modes": [
        "poetry_first",
        "theme_summary",
        "motif_inventory",
        "semantic_explanation",
        "template_slot_filling",
    ],
}


LEARNING_SOURCE_CONTRACT: list[dict[str, str]] = [
    {
        "source": "lyric_behavior_corpus",
        "learns": "line length bands, cadence families, repetition payoff, section pressure transitions",
        "used_for": "section rhythm cells and line behavior constraints",
    },
    {
        "source": "form_family_catalog",
        "learns": "chorus behavior, section order families, release timing",
        "used_for": "form-family selection and section count constraints",
    },
    {
        "source": "artist_style_prior",
        "learns": "hook compression, line attack, cadence preference, lexical roughness",
        "used_for": "grammar bias only, never content filtering",
    },
    {
        "source": "proposition_archetype_bank",
        "learns": "core hook phrase, escalation phrase, release phrase, title-return policy",
        "used_for": "chorus-facing proposition and hook phoneme shape",
    },
    {
        "source": "rhyme_plan",
        "learns": "target tail sounds, section rhyme role, internal rhyme slots",
        "used_for": "natural terminal word candidates and whole-song rhyme grid",
    },
]


TERMINAL_WORD_BANK: dict[str, list[str]] = {
    "る": ["残る", "鳴る", "揺れる", "崩れる", "刺さる", "染みる", "ほどける", "眠る"],
    "い": ["痛い", "近い", "淡い", "深い", "冷たい", "消えない", "細い", "重い"],
    "て": ["ほどけて", "濡れて", "触れて", "裂けて", "揺れて", "壊れて", "黙って", "尖って"],
    "く": ["深く", "遠く", "速く", "きつく", "細く", "低く", "薄く", "強く"],
    "う": ["違う", "向かう", "奪う", "漂う", "迷う", "笑う", "歌う", "揺らぐ"],
    "む": ["沈む", "歪む", "滲む", "刻む", "軋む", "噛む", "拒む", "包む"],
    "ん": ["無音", "余韻", "断線", "終電", "信号音", "体温", "低温", "雑音"],
    "ない": ["戻れない", "離れない", "消えない", "眠れない", "笑えない", "届かない", "ほどけない"],
}


def terminal_words_for_tail_pool(tail_pool: list[Any]) -> dict[str, list[str]]:
    bank: dict[str, list[str]] = {}
    for raw_tail in tail_pool:
        tail = safe_text(raw_tail)
        if not tail:
            continue
        words = TERMINAL_WORD_BANK.get(tail)
        if not words:
            continue
        bank[tail] = list(words)
    return bank


def _line_attack_mode(artist_grammar_bias: dict[str, Any]) -> str:
    attack = safe_text(artist_grammar_bias.get("line_attack"), "balanced")
    if attack in {"hard", "sharp"}:
        return "hard_consonant_attack"
    if attack == "pointed":
        return "pointed_phrase_attack"
    return "clear_vowel_attack"


def _hook_repeat_shape(form_family_id: str, hook_density: str) -> str:
    if form_family_id == "compressed_hook":
        return "call_call_turn_cut"
    if hook_density == "high":
        return "statement_call_call_release"
    return "statement_call_pressure_call_release"


def _section_rhythm_cells(section: str, line_target: int, form_family_id: str) -> list[str]:
    if section in {"chorus", "chorus_final"}:
        if form_family_id == "compressed_hook":
            base = ["2+2 hook call", "2+2 hook call", "3+3 pressure turn", "2+3 cut"]
            if section == "chorus_final":
                base += ["3+3 release push", "3+3 irreversible landing"]
            return base[:line_target]
        base = ["4+4 statement", "2+2 hook call", "3+3 pressure", "2+2 hook call", "4+4 release"]
        return base[:line_target]
    if section in {"pre_chorus", "pre_chorus_2"}:
        base = ["3+3 lift", "3+3 lift"]
        if line_target >= 3:
            base.append("4+3 pressure hold")
        return base[:line_target]
    if section == "bridge":
        return ["4+4 withhold", "3+3 sensory turn", "2+3 breath gap"][:line_target]
    if section == "outro":
        return ["3+3 residue", "3+3 fade", "2+3 tail echo"][:line_target]
    base = ["3+3 image attack", "3+3 body echo", "4+3 pressure hint", "3+3 tail answer"]
    return base[:line_target]


def _syntax_patterns_for_section(section: str) -> list[str]:
    if section in {"chorus", "chorus_final"}:
        return [
            "<core_phrase> + short verb phrase",
            "<core_phrase> + pressure verb",
            "<escalation_or_release_phrase> as sung landing",
        ]
    if section in {"pre_chorus", "pre_chorus_2"}:
        return [
            "<small sensory atom> + <rising verb>",
            "<mechanical/pressure atom> + <tight verb ending>",
        ]
    if section == "bridge":
        return [
            "<viewpoint delay> + <withheld verb>",
            "<single sensory turn> + <breath gap>",
        ]
    if section == "outro":
        return [
            "<residue atom> + <soft terminal verb>",
            "<tail echo> + <fade verb>",
        ]
    return [
        "<scene atom> + <body reaction>",
        "<body atom> + <short verb ending>",
        "<same semantic field> + <tail echo>",
    ]


def _avoid_modes_for_section(section: str) -> list[str]:
    avoid = ["explanatory_clause", "noun_inventory", "abstract_summary"]
    if section not in {"chorus", "chorus_final"}:
        avoid.append("full_hook_fragment")
    if section in {"verse_2", "pre_chorus_2"}:
        avoid.append("new_topic")
    if section != "chorus_final":
        avoid.append("irreversible_release_wording")
    return avoid


def _section_tail_words(card: dict[str, Any], global_bank: dict[str, list[str]]) -> list[str]:
    words: list[str] = []
    for tail in card.get("target_tail_pool", []):
        words.extend(global_bank.get(safe_text(tail), []))
    return unique_preserve_order(words)[:8]


def _line_end_grid(card: dict[str, Any], global_bank: dict[str, list[str]]) -> list[dict[str, Any]]:
    line_target = int(card.get("line_target", 4) or 4)
    pattern = [safe_text(value) for value in card.get("tail_sound_pattern", []) if safe_text(value)]
    pool = [safe_text(value) for value in card.get("target_tail_pool", []) if safe_text(value)]
    if not pattern:
        pattern = ["A"] * line_target
    if not pool:
        pool = ["る", "い", "て"]

    label_counts = {label: pattern.count(label) for label in set(pattern)}
    label_to_tail: dict[str, str] = {}
    next_pool_index = 0
    grid: list[dict[str, Any]] = []
    for index in range(line_target):
        label = pattern[index] if index < len(pattern) else pattern[-1]
        if label not in label_to_tail:
            label_to_tail[label] = pool[min(next_pool_index, len(pool) - 1)]
            next_pool_index += 1
        tail = label_to_tail[label]
        grid.append(
            {
                "line_index": index + 1,
                "pattern_label": label,
                "tail_sound": tail,
                "allowed_terminal_words": list(global_bank.get(tail, []))[:6],
                "must_end_with_terminal_word": True,
                "required_for_validation": label_counts.get(label, 0) >= 2,
            }
        )
    return grid


def build_vocal_material_plan(
    *,
    artist_id: str,
    mode_id: str,
    proposition: dict[str, Any],
    form_plan: dict[str, Any],
    section_behavior_plan: list[dict[str, Any]],
    rhyme_plan: dict[str, Any],
    artist_grammar_bias: dict[str, Any],
) -> dict[str, Any]:
    form_family_id = safe_text(form_plan.get("form_family_id"))
    hook_density = safe_text(proposition.get("hook_density_target"), "medium")
    tail_pool = list(rhyme_plan.get("tail_sound_pool", []))
    terminal_bank = terminal_words_for_tail_pool(tail_pool)
    line_attack = _line_attack_mode(artist_grammar_bias)

    rhythm_cell_plan: list[dict[str, Any]] = []
    line_realization_plan: list[dict[str, Any]] = []
    section_line_end_grid: dict[str, list[dict[str, Any]]] = {}
    for card in section_behavior_plan:
        if not isinstance(card, dict):
            continue
        section = safe_text(card.get("section"))
        if not section:
            continue
        line_target = int(card.get("line_target", 4) or 4)
        rhythm_cells = _section_rhythm_cells(section, line_target, form_family_id)
        section_tail_words = _section_tail_words(card, terminal_bank)
        line_end_grid = _line_end_grid(card, terminal_bank)
        section_line_end_grid[section] = line_end_grid
        rhythm_cell_plan.append(
            {
                "section": section,
                "line_target": line_target,
                "rhythm_cells": rhythm_cells,
                "breath_cut": "hard_cut" if section in {"chorus", "chorus_final", "pre_chorus_2"} else "clean_cut",
                "line_attack_mode": line_attack,
                "tail_sound_pattern": list(card.get("tail_sound_pattern", [])),
                "target_tail_pool": list(card.get("target_tail_pool", [])),
                "line_end_grid": line_end_grid,
            }
        )
        line_realization_plan.append(
            {
                "section": section,
                "section_role": safe_text(card.get("section_role")),
                "pressure_stage": safe_text(card.get("pressure_stage")),
                "syntax_patterns": _syntax_patterns_for_section(section),
                "terminal_word_candidates": section_tail_words,
                "line_end_grid": line_end_grid,
                "allowed_lexical_families": list(card.get("allowed_lexical_families", [])),
                "avoid": _avoid_modes_for_section(section),
            }
        )

    core_phrase = safe_text(proposition.get("core_phrase"))
    return {
        "plan_id": f"{safe_text(artist_id)}:{safe_text(mode_id)}:{safe_text(proposition.get('proposition_id'))}:{form_family_id}:vocal_material",
        "songwriter_identity_contract": dict(SONGWRITER_IDENTITY_CONTRACT),
        "learning_source_contract": [dict(item) for item in LEARNING_SOURCE_CONTRACT],
        "priority_order": list(SONGWRITER_IDENTITY_CONTRACT["priority_order"]),
        "hook_phoneme_shape": {
            "core_phrase": core_phrase,
            "call_unit": core_phrase,
            "repeat_shape": _hook_repeat_shape(form_family_id, hook_density),
            "attack_policy": line_attack,
            "release_phrase": safe_text(proposition.get("release_phrase")),
        },
        "rhythm_cell_plan": rhythm_cell_plan,
        "line_realization_plan": line_realization_plan,
        "section_line_end_grid": section_line_end_grid,
        "minimum_line_end_alignment": 0.55,
        "terminal_word_bank": terminal_bank,
        "forbidden_realization_modes": list(SONGWRITER_IDENTITY_CONTRACT["forbidden_modes"]),
    }
