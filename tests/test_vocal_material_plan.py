from src.akira_engine.vocal_material_plan import (
    SONGWRITER_IDENTITY_CONTRACT,
    build_vocal_material_plan,
    terminal_words_for_tail_pool,
)


def test_terminal_words_for_tail_pool_maps_sounds_to_natural_words():
    bank = terminal_words_for_tail_pool(["る", "い", "て", "unknown"])

    assert "残る" in bank["る"]
    assert "痛い" in bank["い"]
    assert "ほどけて" in bank["て"]
    assert "unknown" not in bank
    assert all(word != tail for tail, words in bank.items() for word in words)


def test_build_vocal_material_plan_outputs_songwriter_first_contract():
    proposition = {
        "proposition_id": "prop_1",
        "core_phrase": "ピンク",
        "hook_density_target": "high",
        "release_phrase": "戻れない",
    }
    form_plan = {
        "form_family_id": "compressed_hook",
        "section_order": ["verse_1", "chorus"],
        "line_target_profile": [4, 4],
    }
    section_behavior_plan = [
        {
            "section": "verse_1",
            "section_role": "world_placement",
            "pressure_stage": "set",
            "line_target": 4,
            "tail_sound_pattern": ["A", "A", "B", "A"],
            "target_tail_pool": ["る", "い"],
            "allowed_lexical_families": ["urban", "body"],
        },
        {
            "section": "chorus",
            "section_role": "proposition_delivery",
            "pressure_stage": "impact",
            "line_target": 4,
            "tail_sound_pattern": ["A", "A", "B", "A"],
            "target_tail_pool": ["る", "く"],
            "allowed_lexical_families": ["collapse", "body"],
        },
    ]
    rhyme_plan = {
        "tail_sound_pool": ["る", "い", "く"],
        "section_rhyme_specs": [],
    }

    plan = build_vocal_material_plan(
        artist_id="maretu",
        mode_id="dark_cute_breakdown",
        proposition=proposition,
        form_plan=form_plan,
        section_behavior_plan=section_behavior_plan,
        rhyme_plan=rhyme_plan,
        artist_grammar_bias={"line_attack": "hard"},
    )

    assert SONGWRITER_IDENTITY_CONTRACT["role"] == "utaite_vocaloid_singer_songwriter"
    assert plan["songwriter_identity_contract"]["primary_output"] == "vocal_material"
    assert plan["hook_phoneme_shape"]["repeat_shape"] == "call_call_turn_cut"
    assert plan["rhythm_cell_plan"][1]["rhythm_cells"][0] == "2+2 hook call"
    assert plan["section_line_end_grid"]["verse_1"][0]["tail_sound"] == "る"
    assert plan["section_line_end_grid"]["verse_1"][1]["tail_sound"] == "る"
    assert plan["section_line_end_grid"]["verse_1"][2]["tail_sound"] == "い"
    assert plan["section_line_end_grid"]["verse_1"][0]["required_for_validation"] is True
    assert plan["section_line_end_grid"]["verse_1"][2]["required_for_validation"] is False
    assert plan["line_realization_plan"][0]["terminal_word_candidates"]
    assert plan["line_realization_plan"][0]["line_end_grid"][0]["allowed_terminal_words"]
    assert "semantic_explanation" in plan["forbidden_realization_modes"]
