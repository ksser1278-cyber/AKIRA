from __future__ import annotations
from typing import Any
from .critic.mod import run_critic_stage, CriticResult
from .production_policy import BASELINE_2026_03_31 as Policy

def score_demo_candidate(plan: dict[str, Any], candidate: dict[str, Any], base_critique: dict[str, Any]) -> dict[str, Any]:
    """
    Backward-compatible wrapper for the canonical Stage I: Critic.
    Refactored for AKIRA ENGINE 90-Day Roadmap (Phase 1).
    """
    # Execute Canonical Stage
    result: CriticResult = run_critic_stage(plan, candidate)
    
    # Map Canonical Result to Legacy Demo Schema
    scores = result.scores
    # demo_critic expects some historically named keys
    scores["adjusted_total"] = scores["total"]
    scores["japanese_char_ratio"] = round(scores["japanese_char_ratio"], 3)
    scores["latin_token_ratio"] = round(scores["latin_token_ratio"], 3)
    
    # Merge Diagnostics into legacy scores if needed
    scores["template_hits"] = len(result.diagnostics.get("template_hits", []))
    
    return {
        "candidate_id": result.candidate_id,
        "title": candidate.get("title", ""),
        "scores": scores,
        "notes": result.notes,
        "critic_notes": result.notes,
        "hard_gate": {
            "passed": result.hard_gate.passed,
            "reasons": result.hard_gate.reasons
        }
    }
