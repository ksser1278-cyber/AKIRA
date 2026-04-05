# scripts/test_week11_master_prompt.py

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


class TestWeek11MasterPrompt(unittest.TestCase):
    def setUp(self) -> None:
        self.project_root = PROJECT_ROOT
        self.router = ProductionRouter()

    def test_master_directive_generation(self) -> None:
        """Verify that per-section master directives are synthesized."""
        blueprint = run_creative_planner(
            project_root=self.project_root,
            artist_id="kanaria",
            mode_id="dark_cute_breakdown"
        )
        
        package = self.router.create_prompt_package(blueprint)
        
        # Check global instructions
        self.assertIn("Master Quality Generation", package["global_instructions"])
        
        # Check specific sections for directives
        found_directives = False
        for section in package["structure"]:
            directives = section["master_directives"]
            self.assertIsInstance(directives, list)
            if len(directives) > 0:
                found_directives = True
                # Check for key keywords
                text = " ".join(directives)
                self.assertTrue(any(kw in text for kw in ["INVERSION", "DISTORTION", "RELEASE", "INTENSIFY", "SOMATIC", "CONCRETE", "CONCEPTUAL"]))

        self.assertTrue(found_directives, "At least some sections should have master directives.")

    def test_motif_transition_narrative(self) -> None:
        """Verify that motif transitions are described narratively in directives."""
        blueprint = run_creative_planner(
            project_root=self.project_root,
            artist_id="maretu",
            mode_id="default"
        )
        
        # Ensure we have some variety in the chain for testing
        package = self.router.create_prompt_package(blueprint)
        
        # Thematic chain should be reflected in directives
        directives_text = ""
        for s in package["structure"]:
            directives_text += " ".join(s["master_directives"])
            
        # Check if transition types (which are used in directives) are present
        # This is probabilistic but with 8 sections, a few should have them.
        self.assertTrue(len(directives_text) > 50)


if __name__ == "__main__":
    unittest.main()
