# scripts/test_sprint_regression.py
"""Day 11 — Sprint Regression Test.

Validates ALL stabilization work in a single pass:
1. Originality/Admission separation
2. Diversity constraints
3. Failure fixtures
4. Hook grammar safety
5. Motif pruning parameters
6. Ops report generation
7. Engine/Routing architecture
"""

from __future__ import annotations

import unittest
import sys
import io
import json
import shutil
import time
from pathlib import Path
from collections import Counter

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from src.akira_engine.creative.canon.admission import CanonAdmissionEngine
from src.akira_engine.creative.canon.policies import AdmissionPolicy, AdmissionStatus
from src.akira_engine.creative.canon.constraints import check_diversity_constraints
from src.akira_engine.critic.originality import calculate_originality_metrics
from src.akira_engine.corpus_intelligence.hooks.policies import check_hook_safety
from src.akira_engine.corpus_intelligence.metadata import create_artifact_metadata
from src.akira_engine.execution.routing import ProductionRouter
from src.akira_engine.execution.prompt_builder import build_section_directives, build_master_instructions


class TestOriginalityAdmissionSeparation(unittest.TestCase):
    """Verify Originality (metrics) and Admission (policy) are cleanly separated."""

    def test_originality_returns_metrics_only(self):
        """calculate_originality_metrics returns numbers, not decisions."""
        result = calculate_originality_metrics(
            {"motifs": ["A", "B"], "hooks": [], "imagery": []},
            [{"motifs": ["A", "C"], "hooks": [], "imagery": [], "track_id": "x"}]
        )
        self.assertIn("composite_originality", result)
        self.assertIn("nearest_neighbor_similarity", result)
        self.assertIn("cliche_density", result)
        # Must NOT contain admission decisions
        self.assertNotIn("status", result)
        self.assertNotIn("admitted", result)

    def test_policy_returns_status_and_reasons(self):
        """AdmissionPolicy.evaluate returns status enum + reason codes."""
        status, reasons = AdmissionPolicy.evaluate({
            "craft_score": 50.0,
            "grounding_intensity": 0.3,
            "composite_originality": 0.2
        })
        self.assertIsInstance(status, AdmissionStatus)
        self.assertIsInstance(reasons, list)
        self.assertTrue(len(reasons) > 0)

    def test_high_originality_low_craft_rejected(self):
        """Originality high + craft low → canon reject."""
        status, reasons = AdmissionPolicy.evaluate({
            "craft_score": 60.0,
            "grounding_intensity": 0.8,
            "composite_originality": 0.9
        })
        self.assertEqual(status, AdmissionStatus.REJECT)
        self.assertIn("low_craft_score", reasons)

    def test_high_craft_low_originality_blocked(self):
        """Craft high + originality low → canon block."""
        status, reasons = AdmissionPolicy.evaluate({
            "craft_score": 95.0,
            "grounding_intensity": 0.9,
            "composite_originality": 0.2
        })
        self.assertIn(status, [AdmissionStatus.REJECT, AdmissionStatus.HOLD])
        self.assertIn("low_originality", reasons)


class TestDiversityConstraints(unittest.TestCase):
    """Verify diversity quotas work on recent canon."""

    def test_cluster_quota_enforcement(self):
        """25% cluster quota on recent 100."""
        # 26 of 100 from same cluster = 26% > 25%
        pool = [{"cluster_id": "X"} for _ in range(26)] + [{"cluster_id": f"Y{i}"} for i in range(74)]
        result = check_diversity_constraints({"cluster_id": "X"}, pool)
        self.assertFalse(result["passed"])
        self.assertIn("cluster_quota_exceeded", result["reasons"])

    def test_hook_continuity_limit(self):
        """Same hook 3 times consecutive → blocked."""
        pool = [{"hooks": ["H1"]} for _ in range(3)]
        result = check_diversity_constraints({"hooks": ["H1"]}, pool)
        self.assertFalse(result["passed"])
        self.assertIn("hook_grammar_continuity_limit", result["reasons"])


class TestHookGrammarSafety(unittest.TestCase):
    """Verify hook grammar doesn't become a copy template."""

    def test_consecutive_pattern_blocked(self):
        recent = [{"pattern": "7-5-7-5"} for _ in range(3)]
        result = check_hook_safety({"pattern": "7-5-7-5", "exclamation_count": 0, "token_count": 10}, recent)
        self.assertFalse(result["safe"])
        self.assertIn("hook_pattern_consecutive_limit", result["violations"])

    def test_exclamation_overuse_flagged(self):
        result = check_hook_safety(
            {"pattern": "7-5", "exclamation_count": 5, "token_count": 10},
            []
        )
        self.assertFalse(result["safe"])
        self.assertIn("hook_exclamation_overuse", result["violations"])


class TestMotifPruningParameters(unittest.TestCase):
    """Verify motif graph builder has tighter parameters."""

    def test_graph_builder_signature(self):
        from src.akira_engine.corpus_intelligence.motifs.graph import build_motif_transition_graph
        import inspect
        sig = inspect.signature(build_motif_transition_graph)
        params = sig.parameters
        self.assertIn("min_support_count", params)
        self.assertIn("min_confidence", params)
        self.assertIn("max_unknown_ratio", params)
        self.assertIn("max_weirdness_per_node", params)
        # Verify defaults are tightened
        self.assertEqual(params["min_support_count"].default, 3)
        self.assertGreaterEqual(params["min_confidence"].default, 0.3)


class TestArtifactMetadata(unittest.TestCase):
    """Verify metadata helper works."""

    def test_metadata_creation(self):
        meta = create_artifact_metadata(
            artifact_type="motif_graph",
            record_count=165,
            source_paths=["a.json", "b.json"]
        )
        self.assertEqual(meta["schema_version"], "2.0")
        self.assertIn("build_version", meta)
        self.assertIn("source_manifest_hash", meta)
        self.assertIn("build_timestamp", meta)
        self.assertEqual(meta["record_count"], 165)


class TestOpsReporting(unittest.TestCase):
    """Verify ops report generates without errors."""

    def test_summary_generation(self):
        from scripts.ops.build_weekly_summary import build_summary
        summary = build_summary(PROJECT_ROOT)
        metrics = summary["metrics"]
        # All 10 keys present
        self.assertIn("1_imagery_coverage_avg", metrics)
        self.assertIn("2_originality_score_avg", metrics)
        self.assertIn("3_imitation_risk_avg", metrics)
        self.assertIn("4_nn_similarity_distribution", metrics)
        self.assertIn("5_canon_admission_rate", metrics)
        self.assertIn("6_cluster_distribution", metrics)
        self.assertIn("7_hook_grammar_distribution", metrics)
        self.assertIn("8_hard_fail_count", metrics)
        self.assertIn("9_hold_count", metrics)
        self.assertIn("10_grade_distribution", metrics)


class TestArchitectureSRP(unittest.TestCase):
    """Verify routing and prompt_builder are properly separated."""

    def test_routing_has_no_directive_logic(self):
        """routing.py should delegate to prompt_builder."""
        import inspect
        from src.akira_engine.execution import routing
        source = inspect.getsource(routing)
        # Routing should NOT contain directive text
        self.assertNotIn("INVERSION:", source)
        self.assertNotIn("DISTORTION:", source)
        self.assertNotIn("CONCEPTUAL PEAK", source)

    def test_prompt_builder_has_directive_logic(self):
        """prompt_builder.py should contain directive text."""
        import inspect
        from src.akira_engine.execution import prompt_builder
        source = inspect.getsource(prompt_builder)
        self.assertIn("INVERSION:", source)
        self.assertIn("CONCRETE NARRATIVE", source)

    def test_runner_exists_and_has_io(self):
        """runner.py should handle I/O."""
        import inspect
        from src.akira_engine.creative import runner
        source = inspect.getsource(runner)
        self.assertIn("_save_blueprint", source)
        self.assertIn("_append_log", source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
