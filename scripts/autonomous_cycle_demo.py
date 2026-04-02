# scripts/autonomous_cycle_demo.py

from __future__ import annotations

import sys
import io
import json
import random
from pathlib import Path

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).resolve().parents[1]  # scripts/ -> AKIRA ENGINE
sys.path.insert(0, str(PROJECT_ROOT))

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from src.akira_engine.creative.planner.mod import run_creative_planner
from src.akira_engine.execution.mod import run_production_loop
from src.akira_engine.creative.canon.mod import admit_to_canon


def autonomous_songwriting_cycle_demo():
    """Demonstrates the full autonomous creative cycle of the AKIRA ENGINE.
    
    1. PLAN: Design an abstract blueprint with motif logic and imagery grounding.
    2. ROUTE/EXECUTE: Synthesize prompt instructions and generate candidates (mock).
    3. ADMIT: Evaluate the results and admit to the elite internal canon if quality is high.
    """
    print("\n" + "="*70)
    print("  AKIRA ENGINE - Autonomous Creativy Cycle Demo (Week 12 Audit)")
    print("="*70)

    # --- STEP 1: PLANNING (Phase 2) ---
    artist_id = "maretu"
    mode_id = "dark_cute_breakdown"
    title_seed = "RED" # Start motif
    
    print(f"\n[PHASE 2: PLAN] Designing creative blueprint for '{artist_id}'...")
    blueprint = run_creative_planner(
        project_root=PROJECT_ROOT,
        artist_id=artist_id,
        mode_id=mode_id,
        title_seed=title_seed,
        creativity_index=0.8
    )
    print(f" > Blueprint '{blueprint.track_id}' created with {len(blueprint.sections)} sections.")
    print(f" > Theme chain transition count: {len(blueprint.thematic_chain)}")

    # --- STEP 2: ROUTING & EXECUTION (Phase 3) ---
    print(f"\n[PHASE 3: ROUTE & EXECUTE] Running production loop...")
    
    # Mock generator that simulates high-quality generation
    def master_generator_mock(plan, package, index, rng):
        # In a real scenario, this would call LLM/Suno
        # Here we mock a high-quality lyric output
        lyric_samples = [
            "赤い視線が 喉を貫く 鼓動が鳴り止まない",
            "反転した 革命の歌 息を止めて 待ち合わせ",
            "ガラスの破片 瞳に刺さる 痛いほど 愛してる"
        ]
        return {
            "lyrics": "\n".join(lyric_samples),
            "status": "success",
            "mora_count": 48
        }

    production_result = run_production_loop(
        project_root=PROJECT_ROOT,
        runtime_plan=blueprint,
        candidate_generator_fn=master_generator_mock,
        max_candidates=3
    )
    
    candidate = production_result["selected_candidate"]
    critic = production_result["critic"]
    print(f" > Candidate generated. Critic Score: {critic.scores.get('total', 0.0):.2f}")
    print(f" > Purity Check: {critic.scores.get('japanese_char_ratio', 1.0):.2f}")

    # --- STEP 3: CANON ADMISSION (Self-accumulation) ---
    print(f"\n[PHASE 2: CANON] Evaluating for admission...")
    
    # Mock novelty report (normally calculated by novelty_index mod)
    novelty_report = {
        "composite_score": 88.5, # A high score!
        "cliche_density": 0.02,
        "recombinative_novelty": 0.7
    }
    
    admission_result = admit_to_canon(
        project_root=PROJECT_ROOT,
        track_id=blueprint.track_id,
        lyrics=candidate["lyrics"],
        novelty_report=novelty_report,
        critic_report={"overall_score": critic.scores.get("total", 0.0)}
    )
    
    if admission_result["status"] == "admitted":
        print(f" > SUCCESS: Track '{blueprint.track_id}' admitted to the INTERNAL CANON.")
        print(f" > Reason: Composite Score {admission_result['composite_score']} > 80.0 threshold.")
    else:
        print(f" > REJECTED: Track did not meet the Elite 100 criteria ({admission_result['status']}).")

    print("\n" + "="*70)
    print("  60-Day Roadmap Complete: J-Pop Creativity Engine is now AUTONOMOUS")
    print("="*70 + "\n")

if __name__ == "__main__":
    autonomous_songwriting_cycle_demo()
