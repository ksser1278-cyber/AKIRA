# scripts/test_week7_narrative.py

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

from src.akira_engine.creative.planner.engine import CreativePlannerEngine
from src.akira_engine.creative.planner.schema import AbstractBlueprint


class TestWeek7Narrative(unittest.TestCase):
    def setUp(self) -> None:
        self.project_root = PROJECT_ROOT
        self.engine = CreativePlannerEngine(self.project_root)

    def test_narrative_intent_assignment(self) -> None:
        """Verify that sections have the correct narrative intent."""
        blueprint = self.engine.design_blueprint(artist_id="kanaria", mode_id="default")
        
        # Check specific sections
        section_intents = {s.section_name: s.narrative_intent for s in blueprint.sections}
        
        self.assertEqual(section_intents.get("intro"), "setup")
        self.assertEqual(section_intents.get("chorus"), "climax")
        self.assertEqual(section_intents.get("bridge"), "twist")
        self.assertEqual(section_intents.get("outro"), "resolution")

    def test_abstraction_ceiling_hierarchy(self) -> None:
        """Verify that abstraction ceilings are dynamically adjusted."""
        blueprint = self.engine.design_blueprint(artist_id="pinocchiop", mode_id="default")
        
        # Chorus should have higher ceiling (more abstract) than Intro
        intro = next(s for s in blueprint.sections if s.section_name == "intro")
        chorus = next(s for s in blueprint.sections if s.section_name == "chorus")
        
        self.assertGreater(chorus.abstraction_ceiling, intro.abstraction_ceiling)
        self.assertEqual(intro.abstraction_ceiling, 0.15)
        self.assertEqual(chorus.abstraction_ceiling, 0.35)

    def test_motif_transition_types_in_chain(self) -> None:
        """Verify that thematic chain contains transition types."""
        blueprint = self.engine.design_blueprint(artist_id="maretu", mode_id="default")
        
        self.assertTrue(len(blueprint.thematic_chain) > 0)
        for trans in blueprint.thematic_chain:
            self.assertIn("transition_type", trans)
            self.assertIn("src_motif", trans)
            self.assertIn("dst_motif", trans)


if __name__ == "__main__":
    unittest.main()
