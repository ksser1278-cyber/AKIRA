"""Integration Test: Week 7 - Full Autonomous Planner Review.

Generates a complete Abstract Blueprint for a song using all Phase 1 
intelligence and Phase 2 narrative logic. Saves the resulting plan 
to the creative_plans directory.
"""

import sys
import io
import json
from pathlib import Path

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).resolve().parents[1]  # scripts/ -> AKIRA ENGINE
sys.path.insert(0, str(PROJECT_ROOT))

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from src.akira_engine.creative.planner.mod import run_creative_planner

def run_integration_test():
    print("===========================================================")
    print("  AKIRA ENGINE - Week 7 Integration: Autonomous Planner")
    print("===========================================================")

    # 1. Generate a Plan
    artist_id = "kanaria"
    mode_id = "dark_cute_breakdown"
    title_seed = "KING"
    
    print(f"Generating creative plan for '{artist_id}' in '{mode_id}' mode...")
    
    blueprint = run_creative_planner(
        project_root=PROJECT_ROOT,
        artist_id=artist_id,
        mode_id=mode_id,
        title_seed=title_seed,
        creativity_index=0.7 # High creativity
    )

    # 2. Save Plan to outputs
    output_dir = PROJECT_ROOT / "outputs" / "creative_plans"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = output_dir / f"{blueprint.track_id}_blueprint.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(blueprint.to_dict(), f, ensure_ascii=False, indent=2)

    print(f"\nPlan Results:")
    print(f" - Track ID: {blueprint.track_id}")
    print(f" - Primary Cluster: {blueprint.primary_cluster}")
    print(f" - Theme Chain Length: {len(blueprint.thematic_chain)}")
    print(f" - Sections: {len(blueprint.sections)}")

    # 3. Structural Review
    print("\nBlueprint Structure Review:")
    for s in blueprint.sections:
        print(f" [{s.section_name:12}] func={s.function:10} intent={s.narrative_intent:10} motif={s.primary_motif:12} ceil={s.abstraction_ceiling:.2f} anchors={s.imagery_anchors}")

    print(f"\nPlan saved to: {output_path}")
    print("\nIntegration test complete!")

if __name__ == "__main__":
    run_integration_test()
