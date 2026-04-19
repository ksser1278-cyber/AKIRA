from types import SimpleNamespace

from src.akira_engine.pre_audit.mod import run_pre_audit_stage


def _card(section: str):
    return SimpleNamespace(
        section=section,
        required_imagery=[],
        imagery_focus=[],
        required_motifs=[],
        scene="",
    )


def test_pre_audit_allows_optional_structural_sections():
    conditioning = SimpleNamespace(
        artist_id="deco27",
        normalized_sections=[
            {"section": "intro"},
            {"section": "verse_1"},
            {"section": "pre_chorus"},
            {"section": "chorus"},
            {"section": "verse_2"},
            {"section": "chorus_2"},
            {"section": "bridge"},
            {"section": "chorus_final"},
            {"section": "outro"},
        ],
        imagery_anchors=[],
        prompt_conditioning={},
    )
    plan = SimpleNamespace(
        artist_id="deco27",
        mode_id="dark_cute_breakdown",
        section_cards=[
            _card("intro"),
            _card("verse_1"),
            _card("pre_chorus"),
            _card("chorus"),
            _card("verse_2"),
            _card("bridge"),
            _card("chorus_final"),
            _card("outro"),
        ],
    )

    result = run_pre_audit_stage(conditioning, plan)

    assert result.identity_match is True
    assert result.structural_match == 1.0
    assert all("Structural match" not in diagnostic for diagnostic in result.diagnostics)


def test_pre_audit_ignores_optional_intro_outro_and_second_pre():
    conditioning = SimpleNamespace(
        artist_id="maretu",
        normalized_sections=[
            {"section": "verse_1"},
            {"section": "pre_chorus"},
            {"section": "chorus"},
            {"section": "verse_2"},
            {"section": "chorus_2"},
            {"section": "bridge"},
            {"section": "chorus_final"},
        ],
        imagery_anchors=[],
        prompt_conditioning={},
    )
    plan = SimpleNamespace(
        artist_id="maretu",
        mode_id="dark_cute_breakdown",
        section_cards=[
            _card("intro"),
            _card("verse_1"),
            _card("pre_chorus"),
            _card("chorus"),
            _card("verse_2"),
            _card("pre_chorus_2"),
            _card("bridge"),
            _card("chorus_final"),
            _card("outro"),
        ],
    )

    result = run_pre_audit_stage(conditioning, plan)

    assert result.structural_match == 1.0
    assert all("Structural match" not in diagnostic for diagnostic in result.diagnostics)


def test_pre_audit_treats_second_verse_as_optional_for_reference_alignment():
    conditioning = SimpleNamespace(
        artist_id="maretu",
        normalized_sections=[
            {"section": "verse_1"},
            {"section": "pre_chorus"},
            {"section": "chorus"},
            {"section": "bridge"},
            {"section": "chorus_final"},
        ],
        imagery_anchors=[],
        prompt_conditioning={},
    )
    plan = SimpleNamespace(
        artist_id="maretu",
        mode_id="dark_cute_breakdown",
        section_cards=[
            _card("intro"),
            _card("verse_1"),
            _card("pre_chorus"),
            _card("chorus"),
            _card("verse_2"),
            _card("pre_chorus_2"),
            _card("bridge"),
            _card("chorus_final"),
            _card("outro"),
        ],
    )

    result = run_pre_audit_stage(conditioning, plan)

    assert result.structural_match == 1.0
    assert result.severity == "pass"


def test_pre_audit_treats_final_chorus_alias_from_last_chorus_2():
    conditioning = SimpleNamespace(
        artist_id="deco27",
        normalized_sections=[
            {"section": "verse_1"},
            {"section": "pre_chorus"},
            {"section": "chorus"},
            {"section": "bridge"},
            {"section": "chorus_2"},
        ],
        imagery_anchors=[],
        prompt_conditioning={},
    )
    plan = SimpleNamespace(
        artist_id="deco27",
        mode_id="dark_cute_breakdown",
        section_cards=[
            _card("intro"),
            _card("verse_1"),
            _card("pre_chorus"),
            _card("chorus"),
            _card("verse_2"),
            _card("bridge"),
            _card("chorus_final"),
            _card("outro"),
        ],
    )

    result = run_pre_audit_stage(conditioning, plan)

    assert result.structural_match == 1.0
    assert result.severity == "pass"
