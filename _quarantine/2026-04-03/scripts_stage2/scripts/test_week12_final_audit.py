# scripts/test_week12_final_audit.py

from __future__ import annotations

import unittest
import sys
import io
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


class TestWeek12FinalAudit(unittest.TestCase):
    def setUp(self) -> None:
        self.project_root = PROJECT_ROOT

    def test_end_to_end_creative_cycle_golden_path(self) -> None:
        """Verify the full golden path: Plan -> Route -> Execute -> Admit.
        
        This test uses mocks for the generative renderer but validates 
        all structural transformations between Phase 1, 2, and 3.
        """
        # 1. PLAN
        blueprint = run_creative_planner(
            project_root=self.project_root,
            artist_id="kanaria",
            mode_id="default"
        )
        self.assertEqual(len(blueprint.sections), 8)
        
        # 2. EXECUTE (Mock)
        def mock_gen(plan, package, index, rng):
            return {"lyrics": "Mocked Japanese Lyrics", "status": "success"}

        production_result = run_production_loop(
            project_root=self.project_root,
            runtime_plan=blueprint,
            candidate_generator_fn=mock_gen,
            max_candidates=1
        )
        self.assertIn("selected_candidate", production_result)
        
        # 3. ADMIT
        novelty_report = {
            "composite_score": 90.0, # High elite score
            "cliche_density": 0.01,
            "recombinative_novelty": 0.8
        }
        
        admission = admit_to_canon(
            project_root=self.project_root,
            track_id=blueprint.track_id,
            lyrics=production_result["selected_candidate"]["lyrics"],
            novelty_report=novelty_report
        )
        
        self.assertEqual(admission["status"], "admitted")
        
        # 4. Persistence check
        canon_path = self.project_root / "data" / "canon_tracks" / f"{blueprint.track_id}.json"
        self.assertTrue(canon_path.exists())


if __name__ == "__main__":
    unittest.main()
