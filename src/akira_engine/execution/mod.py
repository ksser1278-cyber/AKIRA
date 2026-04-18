from __future__ import annotations
from dataclasses import replace
import random
import hashlib
from pathlib import Path
from typing import Any
from src.akira_engine.production_policy import BASELINE_2026_03_31 as Policy
from src.akira_engine.critic.mod import CriticResult, run_critic_stage
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
    selection_diagnostics = {}
    failure_reason = None
    
    selection_rollout = runtime_plan_legacy.get("selection_rollout", {}) if isinstance(runtime_plan_legacy, dict) else {}
    use_blended_selection = bool(selection_rollout.get("enable_blended_selection", False))

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
            legacy_total = float(critic.scores.get("legacy_total", critic.scores.get("total", 0.0)))
            musical_total = float(critic.scores.get("musical_total", legacy_total))
            blended_total = float(
                critic.scores.get(
                    "blended_total",
                    round((legacy_total * 0.4) + (musical_total * 0.6), 2),
                )
            )
            promotion_target_total = blended_total if use_blended_selection else legacy_total
            critic_for_promotion = replace(
                critic,
                scores={**critic.scores, "total": promotion_target_total},
            )
            promotion = run_promotion_stage(critic_for_promotion)
            batch_results.append({
                "candidate": c,
                "critic": critic,
                "promotion": promotion,
                "legacy_total": legacy_total,
                "musical_total": musical_total,
                "blended_total": blended_total,
                "score": blended_total,
            })

        if batch_results:
            legacy_winner = max(batch_results, key=lambda x: (x["legacy_total"], x["musical_total"], x["score"]))
            musical_winner = max(batch_results, key=lambda x: (x["musical_total"], x["legacy_total"], x["score"]))
            blended_winner = max(batch_results, key=lambda x: (x["blended_total"], x["legacy_total"], x["musical_total"]))
            selection_diagnostics = {
                "legacy_winner": {
                    "candidate_id": legacy_winner["candidate"].get("candidate_id"),
                    "legacy_total": legacy_winner["legacy_total"],
                    "musical_total": legacy_winner["musical_total"],
                    "blended_total": legacy_winner["blended_total"],
                },
                "musical_winner": {
                    "candidate_id": musical_winner["candidate"].get("candidate_id"),
                    "legacy_total": musical_winner["legacy_total"],
                    "musical_total": musical_winner["musical_total"],
                    "blended_total": musical_winner["blended_total"],
                },
                "blended_winner": {
                    "candidate_id": blended_winner["candidate"].get("candidate_id"),
                    "legacy_total": blended_winner["legacy_total"],
                    "musical_total": blended_winner["musical_total"],
                    "blended_total": blended_winner["blended_total"],
                },
                "shadow_compare": {
                    "legacy_vs_musical_same": legacy_winner["candidate"].get("candidate_id") == musical_winner["candidate"].get("candidate_id"),
                    "legacy_vs_blended_same": legacy_winner["candidate"].get("candidate_id") == blended_winner["candidate"].get("candidate_id"),
                    "musical_vs_blended_same": musical_winner["candidate"].get("candidate_id") == blended_winner["candidate"].get("candidate_id"),
                    "legacy_gap": round(legacy_winner["legacy_total"] - blended_winner["legacy_total"], 2),
                    "musical_gap": round(musical_winner["musical_total"] - blended_winner["musical_total"], 2),
                },
            }

        if use_blended_selection:
            batch_results.sort(key=lambda x: (x["blended_total"], x["legacy_total"], x["musical_total"]), reverse=True)
        else:
            batch_results.sort(key=lambda x: (x["legacy_total"], x["musical_total"], x["blended_total"]), reverse=True)
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
        "selection_mode": "blended_total_with_shadow_compare" if use_blended_selection else "legacy_total_shadow_compare",
        "selected_score": (
            float(best_critic.scores.get("blended_total", best_critic.scores.get("total", 0.0)))
            if (best_critic and use_blended_selection)
            else float(best_critic.scores.get("legacy_total", best_critic.scores.get("total", 0.0))) if best_critic else 0.0
        ),
        "selected_candidate": best_candidate,
        "promotion": best_promotion,
        "critic": best_critic,
        "attempt_history": attempt_history,
        "batch_candidates": [r["candidate"] for r in all_results],
        "batch_critics": [r["critic"] for r in all_results],
        "batch_promotions": [r["promotion"] for r in all_results],
        "selection_diagnostics": selection_diagnostics,
    }

def _safe_print(msg: str):
    import sys
    print(msg, file=sys.stderr)
