from src.akira_engine.critic.mod import _legacy_total_score


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
    )

    assert smoother_profile["evidence_utilization"] == 9.0
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
    )

    assert profile["evidence_utilization"] == 12.0
    assert profile["oral_release"] == 0.0
    assert score > 0
