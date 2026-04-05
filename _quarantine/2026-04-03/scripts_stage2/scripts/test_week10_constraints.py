# scripts/test_week10_constraints.py

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

from src.akira_engine.execution.constraints import TechnicalConstraintManager
from src.akira_engine.execution.routing import ProductionRouter
from src.akira_engine.creative.planner.mod import run_creative_planner


class TestWeek10Constraints(unittest.TestCase):
    def setUp(self) -> None:
        self.project_root = PROJECT_ROOT
        self.manager = TechnicalConstraintManager()

    def test_dynamic_temperature_scaling(self) -> None:
        """Verify that temperature scales with narrative intent."""
        setup_params = self.manager.get_section_parameters("setup", base_temp=0.7)
        climax_params = self.manager.get_section_parameters("climax", base_temp=0.7)
        twist_params = self.manager.get_section_parameters("twist", base_temp=0.7)
        
        self.assertEqual(setup_params["temperature"], 0.6)
        self.assertEqual(climax_params["temperature"], 0.8)
        self.assertEqual(twist_params["temperature"], 0.9)

    def test_density_guidance(self) -> None:
        """Verify that density profiles provide correct guidance."""
        dense_guide = self.manager.get_density_guidance("dense")
        airy_guide = self.manager.get_density_guidance("airy")
        
        self.assertIn("14-22", dense_guide["mora_per_line"])
        self.assertIn("short", airy_guide["instruction"])

    def test_router_integration(self) -> None:
        """Verify that the router injects technical constraints into the prompt package."""
        blueprint = run_creative_planner(
            project_root=self.project_root,
            artist_id="kanaria",
            mode_id="dark_cute_breakdown"
        )
        
        router = ProductionRouter()
        package = router.create_prompt_package(blueprint)
        
        for section in package["structure"]:
            self.assertIn("technical", section)
            self.assertIn("density_guidance", section)
            # Bridge (twist) should have higher temperature than Intro (setup)
            if section["name"] == "bridge":
                self.assertGreater(section["technical"]["temperature"], 0.7)


if __name__ == "__main__":
    unittest.main()
