# scripts/test_week6_grounding.py

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

from src.akira_engine.creative.planner.grounding import ImageryGroundingRegistry
from src.akira_engine.creative.planner.engine import CreativePlannerEngine


class TestWeek6Grounding(unittest.TestCase):
    def setUp(self) -> None:
        self.project_root = PROJECT_ROOT
        self.registry = ImageryGroundingRegistry(self.project_root)

    def test_registry_loading(self) -> None:
        """Verify that atlas and cluster data are loaded."""
        self.assertTrue(len(self.registry.body_pool) > 0)
        self.assertTrue(len(self.registry.cluster_data.get("clusters", [])) > 0)

    def test_contextual_anchors_selection(self) -> None:
        """Verify that anchors are selected based on cluster residency."""
        # cluster_09: concrete_energetic (contains '叫び', '目')
        cluster_id = "cluster_09"
        anchors = self.registry.select_contextual_anchors(cluster_id=cluster_id, count=5)
        
        self.assertEqual(len(anchors), 5)
        
        # Check if they are from the pools
        all_pool = set(self.registry.body_pool) | set(self.registry.scene_pool)
        for a in anchors:
            self.assertIn(a, all_pool)

    def test_planner_integration(self) -> None:
        """Verify that the planner engine uses the new grounding logic."""
        engine = CreativePlannerEngine(self.project_root)
        
        # kanaria is a member of cluster_07/00 etc.
        blueprint = engine.design_blueprint(artist_id="kanaria", mode_id="dark_cute_breakdown")
        
        self.assertEqual(blueprint.target_artist_id, "kanaria")
        self.assertNotEqual(blueprint.primary_cluster, "unknown")
        
        # Check a few sections for anchors
        for section in blueprint.sections[:3]:
            self.assertEqual(len(section.imagery_anchors), 3)
            self.assertIsInstance(section.grounding_intensity, float)


if __name__ == "__main__":
    unittest.main()
