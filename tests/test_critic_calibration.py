from src.akira_engine.critic.mod import (
    _legacy_total_score,
    _line_attack_repeat_score,
    _parse_sections,
    _rhyme_plan_alignment_score,
    _rhyme_flow_score,
)


def test_hybrid_release_legacy_weights_prefer_smoother_candidate():
    smoother_score, smoother_profile = _legacy_total_score(
        form_family_id="hybrid_release",
        surface_score=0.94,
        singability=1.0,
        binding=0.9,
        imagery_cov=0.7,
        line_variety=0.76,
        hook_restraint=0.84,
        structure_score=0.88,
        evidence_utilization=0.58,
        family_diversity=0.82,
        cliche_control=0.82,
        prosodic_flow=0.87,
        hook_memorability=0.86,
        repetition_payoff=0.8,
        section_contrast=0.84,
        oral_friction=0.0,
        rhyme_flow=0.82,
    )
    evidence_heavy_score, _ = _legacy_total_score(
        form_family_id="hybrid_release",
        surface_score=0.94,
        singability=0.91,
        binding=0.88,
        imagery_cov=0.72,
        line_variety=0.73,
        hook_restraint=0.79,
        structure_score=0.9,
        evidence_utilization=0.71,
        family_diversity=0.78,
        cliche_control=0.67,
        prosodic_flow=0.8,
        hook_memorability=0.77,
        repetition_payoff=0.75,
        section_contrast=0.79,
        oral_friction=0.09,
        rhyme_flow=0.52,
    )

    assert smoother_profile["evidence_utilization"] == 3.0
    assert smoother_profile["prosodic_flow"] == 12.0
    assert smoother_profile["rhyme_flow"] == 15.0
    assert smoother_profile["oral_release"] == 2.0
    assert smoother_score > evidence_heavy_score


def test_compressed_hook_legacy_weights_remain_default():
    score, profile = _legacy_total_score(
        form_family_id="compressed_hook",
        surface_score=0.95,
        singability=0.9,
        binding=0.92,
        imagery_cov=0.85,
        line_variety=0.8,
        hook_restraint=0.78,
        structure_score=0.9,
        evidence_utilization=0.8,
        family_diversity=0.75,
        cliche_control=0.9,
        prosodic_flow=0.82,
        hook_memorability=0.9,
        repetition_payoff=0.92,
        section_contrast=0.78,
        oral_friction=0.08,
        rhyme_flow=0.86,
    )

    assert profile["evidence_utilization"] == 4.0
    assert profile["prosodic_flow"] == 12.0
    assert profile["repetition_payoff"] == 10.0
    assert profile["rhyme_flow"] == 15.0
    assert profile["oral_release"] == 0.0
    assert score > 0


def test_rhythm_first_weights_can_beat_higher_evidence_candidate():
    rhythm_forward_score, rhythm_profile = _legacy_total_score(
        form_family_id="compressed_hook",
        surface_score=0.9,
        singability=0.95,
        binding=0.85,
        imagery_cov=0.45,
        line_variety=0.8,
        hook_restraint=0.85,
        structure_score=0.78,
        evidence_utilization=0.45,
        family_diversity=0.75,
        cliche_control=0.8,
        prosodic_flow=0.95,
        hook_memorability=0.95,
        repetition_payoff=0.95,
        section_contrast=0.6,
        oral_friction=0.02,
        rhyme_flow=0.95,
    )
    evidence_forward_score, _ = _legacy_total_score(
        form_family_id="compressed_hook",
        surface_score=0.9,
        singability=0.78,
        binding=0.85,
        imagery_cov=0.9,
        line_variety=0.72,
        hook_restraint=0.8,
        structure_score=0.9,
        evidence_utilization=0.9,
        family_diversity=0.75,
        cliche_control=0.8,
        prosodic_flow=0.65,
        hook_memorability=0.7,
        repetition_payoff=0.65,
        section_contrast=0.7,
        oral_friction=0.05,
        rhyme_flow=0.35,
    )

    assert rhythm_profile["imagery_cov"] == 4.0
    assert rhythm_profile["evidence_utilization"] == 4.0
    assert rhythm_profile["prosodic_flow"] + rhythm_profile["hook_memorability"] + rhythm_profile["repetition_payoff"] == 32.0
    assert rhythm_profile["rhyme_flow"] == 15.0
    assert rhythm_forward_score > evidence_forward_score


def test_line_attack_repeat_rewards_hook_starts_without_exact_duplicate_lines():
    parsed = _parse_sections(
        "\n".join(
            [
                "# ラブドール",
                "[chorus]",
                "ラブドール、まだ",
                "ラブドール、もう",
                "体温が鳴る",
                "ラブドール、落ちる",
                "[chorus_final]",
                "ラブドール、まだ",
                "ラブドール、もう",
            ]
        )
    )

    assert _line_attack_repeat_score("ラブドール", parsed) >= 0.7


def test_rhyme_flow_rewards_whole_song_tail_echoes_outside_chorus():
    rhymed = _parse_sections(
        "\n".join(
            [
                "[verse_1]",
                "きみが鳴る",
                "熱が鳴る",
                "夜が回る",
                "声が鳴る",
                "[pre_chorus]",
                "指がふれる",
                "胸がゆれる",
                "息がふれる",
            ]
        )
    )
    flat = _parse_sections(
        "\n".join(
            [
                "[verse_1]",
                "きみが鳴る",
                "熱が沈む",
                "夜が白い",
                "声が遠い",
                "[pre_chorus]",
                "指が痛い",
                "胸が落ちる",
                "息が消える",
            ]
        )
    )

    expected_sections = ["verse_1", "pre_chorus"]
    assert _rhyme_flow_score(rhymed, expected_sections) > _rhyme_flow_score(flat, expected_sections)
    assert _rhyme_flow_score(rhymed, expected_sections) >= 0.65


def test_rhyme_plan_alignment_rewards_declared_abab_echoes():
    plan = {
        "section_cards": [
            {
                "section": "verse_1",
                "tail_sound_pattern": ["A", "B", "A", "B"],
                "target_tail_pool": ["る", "い"],
            }
        ]
    }
    aligned = _parse_sections(
        "\n".join(
            [
                "[verse_1]",
                "体温が鳴る",
                "夜が白い",
                "鼓動が燃える",
                "声が遠い",
            ]
        )
    )
    broken = _parse_sections(
        "\n".join(
            [
                "[verse_1]",
                "体温が鳴る",
                "夜が沈む",
                "鼓動が白い",
                "声が遠い",
            ]
        )
    )

    assert _rhyme_plan_alignment_score(plan, aligned) > _rhyme_plan_alignment_score(plan, broken)
    assert _rhyme_plan_alignment_score(plan, aligned) == 1.0
