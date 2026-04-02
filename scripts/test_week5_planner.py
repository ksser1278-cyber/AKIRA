# scripts/test_week5_planner.py

from __future__ import annotations

import json
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

from src.akira_engine.creative.planner.mod import run_creative_planner, convert_blueprint_to_legacy_plan
from src.akira_engine.creative.planner.schema import AbstractBlueprint


class TestWeek5Planner(unittest.TestCase):
    def setUp(self) -> None:
        self.project_root = PROJECT_ROOT
        
    def test_run_creative_planner_smoke(self) -> None:
        """Smoke test for the new creative planner."""
        blueprint = run_creative_planner(
            project_root=self.project_root,
            artist_id="kanaria",
            mode_id="dark_cute_breakdown",
            title_seed="EYE"
        )
        
        self.assertIsInstance(blueprint, AbstractBlueprint)
        self.assertEqual(blueprint.target_artist_id, "kanaria")
        self.assertGreater(len(blueprint.sections), 0)
        
        # Check thematic flow (if motif graph exists)
        # If it doesn't exist, it should still fallback to something
        self.assertIsNotNone(blueprint.sections[0].primary_motif)
        
        # Check sections
        section_names = [s.section_name for s in blueprint.sections]
        self.assertIn("chorus", section_names)
        
    def test_legacy_conversion(self) -> None:
        """Test backward compatibility with the existing generation stage."""
        blueprint = run_creative_planner(
            project_root=self.project_root,
            artist_id="pinocchiop",
            mode_id="energetic_pop"
        )
        
        legacy_plan = convert_blueprint_to_legacy_plan(blueprint)
        
        # Check PlanResult fields
        from src.akira_engine.planner.mod import PlanResult
        self.assertIsInstance(legacy_plan, PlanResult)
        self.assertEqual(legacy_plan.track_id, blueprint.track_id)
        self.assertEqual(len(legacy_plan.section_cards), len(blueprint.sections))
        
        # Each section card should have motifs from the blueprint
        for i, card in enumerate(legacy_plan.section_cards):
            self.assertEqual(card.section, blueprint.sections[i].section_name)
            self.assertIn(blueprint.sections[i].primary_motif, card.required_motifs)

    def test_blueprint_serialization(self) -> None:
        """Test to_dict serialization for artifacts/debugging."""
        blueprint = run_creative_planner(
            project_root=self.project_root,
            artist_id="maretu",
            mode_id="dark_cute_breakdown"
        )
        
        data = blueprint.to_dict()
        self.assertEqual(data["track_id"], blueprint.track_id)
        self.assertEqual(data["artist"], "maretu")
        self.assertIsInstance(data["sections"], list)


if __name__ == "__main__":
    unittest.main()
