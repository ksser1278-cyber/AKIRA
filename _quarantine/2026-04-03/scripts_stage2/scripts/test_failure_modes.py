# scripts/test_failure_modes.py
"""Day 4 — Failure-Path Fixtures

5 fixtures that MUST be rejected/held by the engine:
1. Duplicate lyric (near-identical to existing canon)
2. Metadata contamination (English leakage, meta-commentary)
3. Narrative collapse (motifs present but no coherent flow)
4. Empty hooks (only hook grammar, no substance)
5. Too close to recent canon (cluster + motif overlap)
"""

from __future__ import annotations

import unittest
import sys
import io
import json
import shutil
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from src.akira_engine.creative.canon.admission import CanonAdmissionEngine
from src.akira_engine.creative.canon.policies import AdmissionStatus
from src.akira_engine.critic.mod import run_critic_stage


class TestFailureModes(unittest.TestCase):
    """Ensures bad samples are correctly detected and blocked."""

    def setUp(self):
        self.project_root = PROJECT_ROOT
        self.engine = CanonAdmissionEngine(self.project_root)
        self.test_canon = self.project_root / "data" / "canon_tracks_failure_test"
        self.test_canon.mkdir(parents=True, exist_ok=True)
        self.engine.canon_dir = self.test_canon

        # Seed a reference track
        seed = {
            "track_id": "seed_maretu_001",
            "motifs": ["革命", "解放", "痛み", "叫び", "崩壊"],
            "hooks": ["hook_dark_A", "hook_stutter_B"],
            "imagery": ["瞳", "血", "ガラス"],
            "cluster_id": "cluster_03",
            "section_names": ["intro", "verse_1", "chorus", "bridge", "chorus_final"]
        }
        self.engine.admit_track_data("seed_maretu_001", "種のリリック", {}, {"metrics": seed})

    def tearDown(self):
        shutil.rmtree(self.test_canon, ignore_errors=True)

    # ── Fixture 1: Near-Duplicate ──
    def test_fixture_duplicate_lyric(self):
        """A track with identical motifs/hooks/imagery must be rejected."""
        duplicate = {
            "motifs": ["革命", "解放", "痛み", "叫び", "崩壊"],  # 100% overlap
            "hooks": ["hook_dark_A", "hook_stutter_B"],
            "imagery": ["瞳", "血", "ガラス"],
            "cluster_id": "cluster_03"
        }
        status, reasons, _ = self.engine.evaluate_admission(
            duplicate, critic_report={"total_score": 92.0}, grounding_intensity=0.9
        )
        self.assertIn(status, [AdmissionStatus.REJECT, AdmissionStatus.HOLD],
                       f"Duplicate should be blocked but got {status}: {reasons}")

    # ── Fixture 2: Metadata Contamination ──
    def test_fixture_metadata_contamination(self):
        """A lyric full of English meta-commentary must fail critic hard gate."""
        contaminated_lyric = (
            "[Verse 1]\n"
            "This is a placeholder lyric for testing purposes.\n"
            "Genre: Dark Pop | Vocal: Female | BPM: 160\n"
            "The song should express deep sadness and longing.\n"
            "[Chorus]\n"
            "Ready-dy-dy Ga-ga-giga B-B-BPM\n"
        )
        plan = {"section_cards": [], "motif_roster": [], "keywords": []}
        candidate = {"candidate_id": "contaminated_001", "markdown": contaminated_lyric, "title": "Test"}
        
        critic = run_critic_stage(plan, candidate)
        # Must fail hard gate or get very low score
        self.assertTrue(
            not critic.hard_gate.passed or critic.scores.get("total", 100) < 50,
            f"Contaminated lyric should fail: gate={critic.hard_gate.passed}, score={critic.scores.get('total')}"
        )

    # ── Fixture 3: Narrative Collapse ──
    def test_fixture_narrative_collapse(self):
        """Motifs present but no coherent emotional flow — originality may be OK but craft is low."""
        narrative_broken = {
            "motifs": ["花", "星", "雷", "海", "火"],  # Random unrelated motifs
            "hooks": [],
            "imagery": [],
            "section_names": ["chorus", "chorus", "chorus", "chorus"]  # No structure
        }
        status, reasons, metrics = self.engine.evaluate_admission(
            narrative_broken, critic_report={"total_score": 45.0}, grounding_intensity=0.2
        )
        self.assertIn(status, [AdmissionStatus.REJECT, AdmissionStatus.HOLD],
                       f"Narrative collapse should be blocked: {status}, {reasons}")

    # ── Fixture 4: Empty Hooks ──
    def test_fixture_empty_hooks(self):
        """Hook grammar present but lyric has no substance — low craft score."""
        empty_hook_lyric = (
            "[Chorus]\n"
            "ラ ラ ラ ラ ラ ラ ラ\n"
            "(Ah-hah) (Ah-hah) (Ah-hah)\n"
            "ラ ラ ラ\n"
        )
        plan = {"section_cards": [], "motif_roster": [{"motifs": ["革命"]}], "keywords": ["革命"]}
        candidate = {"candidate_id": "empty_hook_001", "markdown": empty_hook_lyric, "title": "ラ"}
        
        critic = run_critic_stage(plan, candidate)
        # Low imagery, low binding, low surface quality
        total = critic.scores.get("total", 100)
        self.assertLess(total, 60.0, f"Empty hook lyric should score low: {total}")

    # ── Fixture 5: Too Close to Recent Canon ──
    def test_fixture_too_close_to_canon(self):
        """A track with 80%+ motif overlap with the most recent canon entry must be rejected."""
        close_track = {
            "motifs": ["革命", "解放", "痛み", "叫び", "新しい"],  # 4/5 overlap = 80%
            "hooks": ["hook_dark_A"],
            "imagery": ["瞳", "血"],
            "cluster_id": "cluster_03"
        }
        status, reasons, _ = self.engine.evaluate_admission(
            close_track, critic_report={"total_score": 88.0}, grounding_intensity=0.8
        )
        self.assertIn(status, [AdmissionStatus.REJECT, AdmissionStatus.HOLD],
                       f"Canon-close track should be blocked: {status}, {reasons}")


if __name__ == "__main__":
    unittest.main()
