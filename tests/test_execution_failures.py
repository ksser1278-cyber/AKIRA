import pytest
import random
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.akira_engine.execution.mod import run_production_loop
from src.akira_engine.critic.mod import CriticResult, HardGate
from src.akira_engine.promotion.mod import PromotionResult
from src.akira_engine.production_policy import BASELINE_2026_03_31 as Policy

@pytest.fixture
def mock_plan():
    return {"track_id": "test_track", "artist_id": "test_artist"}

@pytest.fixture
def mock_prompt():
    return {"instructions": "test"}

def test_zero_candidate_generation(mock_plan, mock_prompt):
    """Verify that if the generator returns nothing, the loop handles it gracefully."""
    def empty_generator(*args, **kwargs):
        return None

    result = run_production_loop(
        project_root=Path("."),
        runtime_plan=mock_plan,
        prompt_package=mock_prompt,
        candidate_generator_fn=empty_generator,
        max_candidates=3
    )

    assert result["ok"] is False
    assert result["failure_reason"] == "no_candidates_generated"
    assert len(result["attempt_history"]) == Policy.MAX_RETRIES + 1
    assert all(a["reason"] == "no_candidates_generated" for a in result["attempt_history"])

def test_hard_gate_failure_and_retry(mock_plan, mock_prompt):
    """Verify that a low-imagery result triggers a retry and eventual failure/success."""
    
    # Mocking generator to return a dummy candidate
    def dummy_generator(*args, **kwargs):
        return {"candidate_id": "c1", "markdown": "lyrics"}

    # Mocking critic to fail on 1st attempt, pass on 2nd
    fail_critic = CriticResult(
        candidate_id="c1",
        hard_gate=HardGate(passed=True),
        scores={"total": 50.0, "imagery_coverage": 0.0, "japanese_char_ratio": 0.9}
    )
    pass_critic = CriticResult(
        candidate_id="c1",
        hard_gate=HardGate(passed=True),
        scores={"total": 85.0, "imagery_coverage": 1.0, "japanese_char_ratio": 0.9}
    )

    promo = PromotionResult(candidate_id="c1", grade="Gold", reason="ok")

    with patch("src.akira_engine.execution.mod.run_critic_stage") as mock_critic:
        with patch("src.akira_engine.execution.mod.run_promotion_stage") as mock_promo:
            # First attempt fails hard gate, second succeeds
            mock_critic.side_effect = [fail_critic, pass_critic]
            mock_promo.return_value = promo

            result = run_production_loop(
                project_root=Path("."),
                runtime_plan=mock_plan,
                prompt_package=mock_prompt,
                candidate_generator_fn=dummy_generator,
                max_candidates=1 # Batch of 1 for simplicity
            )

            assert result["ok"] is True
            assert len(result["attempt_history"]) == 2
            assert result["attempt_history"][0]["reason"] == "hard_gate_failure"
            assert result["attempt_history"][1]["success"] is True

def test_permanent_hard_gate_failure(mock_plan, mock_prompt):
    """Verify manifest state when all retries fail the hard gate."""
    def dummy_generator(*args, **kwargs):
        return {"candidate_id": "c1", "markdown": "lyrics"}

    fail_critic = CriticResult(
        candidate_id="c1",
        hard_gate=HardGate(passed=True),
        scores={"total": 40.0, "imagery_coverage": 0.0, "japanese_char_ratio": 0.9}
    )
    promo = PromotionResult(candidate_id="c1", grade="Fail", reason="hard gate")

    with patch("src.akira_engine.execution.mod.run_critic_stage", return_value=fail_critic):
        with patch("src.akira_engine.execution.mod.run_promotion_stage", return_value=promo):
            result = run_production_loop(
                project_root=Path("."),
                runtime_plan=mock_plan,
                prompt_package=mock_prompt,
                candidate_generator_fn=dummy_generator,
                max_candidates=1
            )

            assert result["ok"] is False
            assert result["failure_reason"] == "hard_gate_failure_final"
            assert len(result["attempt_history"]) == Policy.MAX_RETRIES + 1
            assert result["selected_candidate"] is None


def test_blended_selection_records_shadow_compare(mock_plan, mock_prompt):
    def indexed_generator(*args, **kwargs):
        index = kwargs.get("index", 0)
        return {
            "candidate_id": f"c{index + 1}",
            "markdown": "lyrics",
            "form_family_id": "compressed_hook" if index == 0 else "hybrid_release",
            "renderer_frame_family": "dark_cute_breakdown/compressed_hook" if index == 0 else "dark_cute_breakdown/hybrid_release",
            "chorus_shape": "repeat_punch" if index == 0 else "statement_hook_release",
            "bridge_shape": "withholding_drop" if index == 0 else "perspective_delay",
            "hook_pressure_realized": "high" if index == 0 else "medium",
        }

    critic_legacy = CriticResult(
        candidate_id="c1",
        hard_gate=HardGate(passed=True),
        scores={
            "total": 90.0,
            "legacy_total": 90.0,
            "musical_total": 70.0,
            "blended_total": 78.0,
            "imagery_coverage": 1.0,
            "japanese_char_ratio": 0.95,
        },
    )
    critic_blended = CriticResult(
        candidate_id="c2",
        hard_gate=HardGate(passed=True),
        scores={
            "total": 82.0,
            "legacy_total": 82.0,
            "musical_total": 96.0,
            "blended_total": 90.4,
            "imagery_coverage": 1.0,
            "japanese_char_ratio": 0.95,
        },
    )
    promo = PromotionResult(candidate_id="c2", grade="Gold", reason="ok")

    with patch("src.akira_engine.execution.mod.run_critic_stage") as mock_critic:
        with patch("src.akira_engine.execution.mod.run_promotion_stage") as mock_promo:
            mock_critic.side_effect = [critic_legacy, critic_blended]
            mock_promo.return_value = promo

            result = run_production_loop(
                project_root=Path("."),
                runtime_plan=mock_plan,
                prompt_package=mock_prompt,
                candidate_generator_fn=indexed_generator,
                max_candidates=2,
            )

            assert result["ok"] is True
            assert result["selection_mode"] == "legacy_total_shadow_compare"
            assert result["selected_candidate"]["candidate_id"] == "c1"
            assert result["selected_score"] == pytest.approx(90.0)
            assert result["selection_diagnostics"]["legacy_winner"]["candidate_id"] == "c1"
            assert result["selection_diagnostics"]["blended_winner"]["candidate_id"] == "c2"
            assert result["selection_diagnostics"]["legacy_winner"]["renderer_frame_family"] == "dark_cute_breakdown/compressed_hook"
            assert result["selection_diagnostics"]["blended_winner"]["bridge_shape"] == "perspective_delay"
            assert result["selection_diagnostics"]["rollout_gate"]["recommended"] is True
            assert result["selection_diagnostics"]["rollout_gate"]["candidate_id"] == "c2"


def test_blended_selection_can_be_enabled_via_rollout(mock_prompt):
    runtime_plan = {
        "track_id": "test_track",
        "artist_id": "test_artist",
        "selection_rollout": {"enable_blended_selection": True},
    }

    def indexed_generator(*args, **kwargs):
        index = kwargs.get("index", 0)
        return {
            "candidate_id": f"c{index + 1}",
            "markdown": "lyrics",
            "form_family_id": "compressed_hook" if index == 0 else "hybrid_release",
            "renderer_frame_family": "dark_cute_breakdown/compressed_hook" if index == 0 else "dark_cute_breakdown/hybrid_release",
            "chorus_shape": "repeat_punch" if index == 0 else "statement_hook_release",
            "bridge_shape": "withholding_drop" if index == 0 else "perspective_delay",
            "hook_pressure_realized": "high" if index == 0 else "medium",
        }

    critic_legacy = CriticResult(
        candidate_id="c1",
        hard_gate=HardGate(passed=True),
        scores={
            "total": 90.0,
            "legacy_total": 90.0,
            "musical_total": 70.0,
            "blended_total": 78.0,
            "imagery_coverage": 1.0,
            "japanese_char_ratio": 0.95,
        },
    )
    critic_blended = CriticResult(
        candidate_id="c2",
        hard_gate=HardGate(passed=True),
        scores={
            "total": 82.0,
            "legacy_total": 82.0,
            "musical_total": 96.0,
            "blended_total": 90.4,
            "imagery_coverage": 1.0,
            "japanese_char_ratio": 0.95,
        },
    )
    promo = PromotionResult(candidate_id="c2", grade="Gold", reason="ok")

    with patch("src.akira_engine.execution.mod.run_critic_stage") as mock_critic:
        with patch("src.akira_engine.execution.mod.run_promotion_stage") as mock_promo:
            mock_critic.side_effect = [critic_legacy, critic_blended]
            mock_promo.return_value = promo

            result = run_production_loop(
                project_root=Path("."),
                runtime_plan=runtime_plan,
                prompt_package=mock_prompt,
                candidate_generator_fn=indexed_generator,
                max_candidates=2,
            )

            assert result["ok"] is True
            assert result["selection_mode"] == "blended_total_with_shadow_compare"
            assert result["selected_candidate"]["candidate_id"] == "c2"
            assert result["selected_score"] == pytest.approx(90.4)
