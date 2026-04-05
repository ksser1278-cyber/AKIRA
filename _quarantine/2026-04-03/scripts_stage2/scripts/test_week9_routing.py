# scripts/test_week9_routing.py

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

from src.akira_engine.execution.routing import ProductionRouter
from src.akira_engine.creative.planner.mod import run_creative_planner


class TestWeek9Routing(unittest.TestCase):
    def setUp(self) -> None:
        self.project_root = PROJECT_ROOT
        self.router = ProductionRouter()

    def test_mode_parameter_mapping(self) -> None:
        """Verify that mode-specific parameters are correctly mapped."""
        dark_params = self.router.get_mode_params("dark_cute_breakdown")
        pop_params = self.router.get_mode_params("energetic_pop")
        
        self.assertEqual(dark_params["temperature"], 0.8)
        self.assertEqual(pop_params["temperature"], 0.6)
        self.assertGreater(dark_params["grounding_intensity"], pop_params["grounding_intensity"])

    def test_prompt_package_creation(self) -> None:
        """Verify that a prompt package is correctly built from a blueprint."""
        blueprint = run_creative_planner(
            project_root=self.project_root,
            artist_id="kanaria",
            mode_id="dark_cute_breakdown"
        )
        
        package = self.router.create_prompt_package(blueprint)
        
        self.assertEqual(package["track_id"], blueprint.track_id)
        self.assertEqual(package["technical_params"]["temperature"], 0.8)
        self.assertTrue(len(package["structure"]) > 0)
        self.assertIn(" Glitchy", package["instructions"])

    def test_execution_loop_integration_smoke(self) -> None:
        """Smoke test for run_production_loop with AbstractBlueprint."""
        from src.akira_engine.execution.mod import run_production_loop
        
        blueprint = run_creative_planner(
            project_root=self.project_root,
            artist_id="maretu",
            mode_id="default"
        )
        
        # Mock generator function
        def mock_generator(plan, package, index, rng):
            return {"lyrics": "Dummy lyrics", "status": "success"}
            
        result = run_production_loop(
            project_root=self.project_root,
            runtime_plan=blueprint,
            candidate_generator_fn=mock_generator,
            max_candidates=1
        )
        
        self.assertIn("selected_candidate", result)
        # Verify that prompt_package was automatically created via routing
        self.assertIsNotNone(result["selected_candidate"])


if __name__ == "__main__":
    unittest.main()
