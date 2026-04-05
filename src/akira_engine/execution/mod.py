from __future__ import annotations
import random
import hashlib
from pathlib import Path
from typing import Any
from src.akira_engine.production_policy import BASELINE_2026_03_31 as Policy
from src.akira_engine.critic.mod import run_critic_stage
from src.akira_engine.promotion.mod import run_promotion_stage

from src.akira_engine.execution.routing import ProductionRouter
from src.akira_engine.creative.planner.schema import AbstractBlueprint


def run_production_loop(
    project_root: Path,
    runtime_plan: dict[str, Any] | AbstractBlueprint,
    prompt_package: dict[str, Any] = None,
    *,
    candidate_generator_fn: Any, # Callback to LLM/Renderer
    max_candidates: int = 5,
) -> dict[str, Any]:
    """
    Stage L: Execution Engine (Frozen Production Loop).
    Handles multi-candidate generation, evaluation, and policy-driven retries.
    Refactored from demo_runtime for Stage J consistency.
    Supports Week 9 AbstractBlueprint and ProductionRouter.
    """
    
    # 0. Routing (New Phase 3 step)
    router = ProductionRouter()
    if isinstance(runtime_plan, AbstractBlueprint):
        prompt_package = router.create_prompt_package(runtime_plan)
        # Convert blueprint to legacy for internal compatibility
        from src.akira_engine.creative.planner.mod import convert_blueprint_to_legacy_plan
        from dataclasses import asdict
        runtime_plan_legacy = asdict(convert_blueprint_to_legacy_plan(runtime_plan))
    else:
        runtime_plan_legacy = runtime_plan
        # Ensure prompt package exists
        if not prompt_package:
            prompt_package = {"instructions": "Generate J-Pop lyrics.", "mode": "default", "technical_params": {}}

    # Deterministic RNG
    seed_key = runtime_plan_legacy.get("track_id", "demo") if isinstance(runtime_plan_legacy, dict) else getattr(runtime_plan_legacy, "track_id", "demo")
    seed_string = f"{seed_key}:production"
    rng = random.Random(int(hashlib.md5(seed_string.encode("utf-8")).hexdigest()[:8], 16))
    
    best_candidate = None
    best_promotion = None
    best_critic = None
    all_results = []
    attempt_history = []
    failure_reason = None
    
    # 1. Implementation of Selective Retry (Hard Gate)
    for attempt in range(Policy.MAX_RETRIES + 1):
        candidates = []
        _safe_print(f"[EXEC] Production Attempt {attempt+1}/{Policy.MAX_RETRIES+1}...")
        
        # Adaptive Batching (Policy Driven)
        batch_size = max_candidates
        for i in range(batch_size):
            c = candidate_generator_fn(runtime_plan_legacy, prompt_package, index=i, rng=rng)
            if c: candidates.append(c)
            
        if not candidates:
            attempt_history.append({"attempt": attempt + 1, "success": False, "reason": "no_candidates_generated"})
            failure_reason = "no_candidates_generated"
            continue
            
        # 2. Evaluation & Selection Committee
        batch_results = []
        for c in candidates:
            critic = run_critic_stage(runtime_plan_legacy, c)
            promotion = run_promotion_stage(critic)
            batch_results.append({
                "candidate": c,
                "critic": critic,
                "promotion": promotion,
                "score": critic.scores.get("total", 0.0)
            })
            
        # Sort by Score
        batch_results.sort(key=lambda x: x["score"], reverse=True)
        winner = batch_results[0]
        all_results = batch_results # Preserve last batch
        
        # 3. Hard Gate (Policy Driven)
        # Production Hard Fail: imagery_coverage == 0 OR japanese_ratio < 0.7
        low_imagery = winner["critic"].scores.get("imagery_coverage", 0.0) <= Policy.IMAGERY_COVERAGE_HARD_FAIL_THRESHOLD
        low_purity = winner["critic"].scores.get("japanese_char_ratio", 1.0) < Policy.JAPANESE_RATIO_MIN - 0.1
        
        current_failure = []
        if low_imagery: current_failure.append("low_imagery")
        if low_purity: current_failure.append("low_purity")
        
        if current_failure:
            attempt_history.append({
                "attempt": attempt + 1,
                "success": False,
                "reason": "hard_gate_failure",
                "details": current_failure,
                "best_score": winner["score"]
            })
            if attempt < Policy.MAX_RETRIES:
                _safe_print(f"[HARD GATE] Quality failure ({', '.join(current_failure)}). Retrying...")
                failure_reason = "hard_gate_failure_max_retries"
                continue
            else:
                failure_reason = "hard_gate_failure_final"
        
        # Accept Winner
        best_candidate = winner["candidate"]
        best_promotion = winner["promotion"]
        best_critic = winner["critic"]
        attempt_history.append({
            "attempt": attempt + 1,
            "success": True,
            "score": winner["score"]
        })
        failure_reason = None
        break

    return {
        "schema_version": Policy.PRODUCTION_SCHEMA_VERSION,
        "policy_version": "BASELINE_2026_03_31",
        "ok": best_candidate is not None,
        "failure_reason": failure_reason,
        "selected_candidate": best_candidate,
        "promotion": best_promotion,
        "critic": best_critic,
        "attempt_history": attempt_history,
        "batch_candidates": [r["candidate"] for r in all_results],
        "batch_critics": [r["critic"] for r in all_results],
        "batch_promotions": [r["promotion"] for r in all_results]
    }

def _safe_print(msg: str):
    import sys
    print(msg, file=sys.stderr)
