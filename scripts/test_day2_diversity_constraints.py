# scripts/test_day2_diversity_constraints.py

from __future__ import annotations

import unittest
import sys
import io
import shutil
import json
import time
from pathlib import Path

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).resolve().parents[1]  # scripts/ -> AKIRA ENGINE
sys.path.insert(0, str(PROJECT_ROOT))

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from src.akira_engine.creative.canon.admission import CanonAdmissionEngine
from src.akira_engine.creative.canon.policies import AdmissionStatus


class TestDay2DiversityConstraints(unittest.TestCase):
    def setUp(self) -> None:
        self.project_root = PROJECT_ROOT
        self.engine = CanonAdmissionEngine(self.project_root)
        
        # Temporary test canon
        self.test_canon_dir = self.project_root / "data" / "canon_tracks_diversity_test"
        self.test_canon_dir.mkdir(parents=True, exist_ok=True)
        self.engine.canon_dir = self.test_canon_dir

    def tearDown(self) -> None:
        shutil.rmtree(self.test_canon_dir, ignore_errors=True)

    def test_hook_continuity_rejection(self) -> None:
        """Verify that using the same hook grammar 3 times consecutively leads to rejection."""
        # 1. Add 3 tracks with the same hook
        for i in range(3):
            tid = f"track_{i}"
            features = {
                "track_id": tid,
                "motifs": [f"Motif_{i}"],
                "hooks": ["HOOK_A"], # Same hook
                "cluster_id": f"cluster_{i}"
            }
            self.engine.admit_track_data(tid, "lyrics", {}, {"metrics": features})
            time.sleep(0.01) # Ensure file mtime order

        # 2. Try to admit a 4th track with the same hook
        candidate_features = {
            "motifs": ["UniqueMotif"],
            "hooks": ["HOOK_A"], # 4th consecutive!
            "cluster_id": "new_cluster"
        }
        
        status, reasons, metrics = self.engine.evaluate_admission(
            candidate_features,
            critic_report={"total_score": 90.0},
            grounding_intensity=0.8
        )
        
        self.assertEqual(status, AdmissionStatus.REJECT)
        self.assertIn("hook_grammar_continuity_limit", reasons)

    def test_cluster_quota_rejection(self) -> None:
        """Verify that exceeding cluster quota (25%) leads to rejection.
        Requires at least 20 samples to trigger.
        """
        # 1. Fill 20 slots with 6 from 'cluster_X' (6/20 = 30% > 25%)
        for i in range(20):
            tid = f"p_{i}"
            cid = "cluster_X" if i < 6 else f"cluster_{i}"
            features = {
                "track_id": tid,
                "motifs": [f"M{i}"],
                "hooks": [f"H{i}"],
                "cluster_id": cid
            }
            self.engine.admit_track_data(tid, "lyrics", {}, {"metrics": features})
            time.sleep(0.01)

        # 2. Try to admit 7th track from 'cluster_X'
        candidate_features = {
            "motifs": ["NewM"],
            "hooks": ["NewH"],
            "cluster_id": "cluster_X"
        }
        
        status, reasons, metrics = self.engine.evaluate_admission(
            candidate_features,
            critic_report={"total_score": 90.0},
            grounding_intensity=0.8
        )
        
        self.assertEqual(status, AdmissionStatus.REJECT)
        self.assertIn("cluster_quota_exceeded", reasons)

    def test_underrepresented_bonus(self) -> None:
        """Verify that a rare cluster gets a craft score bonus."""
        # 1. Fill 20 slots, none from 'rare_cluster'
        for i in range(20):
            tid = f"b_{i}"
            self.engine.admit_track_data(tid, "lyrics", {}, {"metrics": {"cluster_id": "common"}})
            
        # 2. Evaluate 'rare_cluster' candidate
        candidate_features = {
            "motifs": ["M"],
            "hooks": ["H"],
            "cluster_id": "rare_cluster"
        }
        
        # Base score 76 (normally REJECT if < 80)
        status, reasons, metrics = self.engine.evaluate_admission(
            candidate_features,
            critic_report={"total_score": 76.0},
            grounding_intensity=0.8
        )
        
        # With +5 bonus, effective craft = 81 -> PASS/HOLD
        self.assertGreater(metrics["craft_score"], 80.0)
        self.assertIn(status, [AdmissionStatus.PASS, AdmissionStatus.WARN, AdmissionStatus.HOLD])
        self.assertEqual(metrics["diversity_bonus"], 5.0)


if __name__ == "__main__":
    unittest.main()
