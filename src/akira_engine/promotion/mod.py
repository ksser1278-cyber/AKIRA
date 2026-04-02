from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from src.akira_engine.critic.mod import CriticResult

@dataclass
class PromotionResult:
    candidate_id: str
    grade: str # Gold, Silver, Hold, Fail
    reason: str = ""

def run_promotion_stage(
    critic_result: CriticResult,
) -> PromotionResult:
    """Execute Stage J: Promotion Engine."""
    from src.akira_engine.production_policy import BASELINE_2026_03_31 as Policy
    
    candidate_id = critic_result.candidate_id
    scores = critic_result.scores
    diagnostics = critic_result.diagnostics
    gate = critic_result.hard_gate
    
    # 1. Failed
    if not gate.passed:
        return PromotionResult(candidate_id, "Fail", f"Hard gate failed: {', '.join(gate.reasons)}")
        
    # Baseline Freeze: Policy Driven Promotion
    total_score = scores.get("total", 0.0)
    jp_ratio = scores.get("japanese_char_ratio", 0.0)
    latin_ratio = scores.get("latin_token_ratio", 1.0)
    imagery_cov = scores.get("imagery_coverage", 0.0)
    
    # 2. Gold check
    is_gold = (
        total_score >= Policy.GOLD_SCORE_THRESHOLD and
        jp_ratio >= Policy.JAPANESE_RATIO_MIN and
        latin_ratio <= Policy.LATIN_TOKEN_RATIO_MAX and
        len(diagnostics.get("template_hits", [])) == 0
    )
    if is_gold:
        return PromotionResult(candidate_id, "Gold", "High-fidelity production grade")
        
    # 3. Silver check
    is_silver = (
        total_score >= Policy.SILVER_SCORE_THRESHOLD and
        jp_ratio >= 0.8 # Slightly looser for Silver
    )
    if is_silver:
        return PromotionResult(candidate_id, "Silver", "Usable quality with minor issues")
        
    return PromotionResult(candidate_id, "Hold", "Audit complete but low quality scores")
