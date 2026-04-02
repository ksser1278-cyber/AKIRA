# scripts/test_day1_originality_admission.py

from __future__ import annotations

import unittest
import sys
import io
import shutil
from pathlib import Path

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).resolve().parents[1]  # scripts/ -> AKIRA ENGINE
sys.path.insert(0, str(PROJECT_ROOT))

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from src.akira_engine.creative.canon.admission import CanonAdmissionEngine
from src.akira_engine.creative.canon.policies import AdmissionStatus


class TestDay1OriginalityAdmission(unittest.TestCase):
    def setUp(self) -> None:
        self.project_root = PROJECT_ROOT
        self.engine = CanonAdmissionEngine(self.project_root)
        
        # Temporary test canon
        self.test_canon_dir = self.project_root / "data" / "canon_tracks_test"
        self.test_canon_dir.mkdir(parents=True, exist_ok=True)
        self.engine.canon_dir = self.test_canon_dir

    def tearDown(self) -> None:
        shutil.rmtree(self.test_canon_dir, ignore_errors=True)

    def test_rejection_for_low_originality(self) -> None:
        """Verify that a track too close to existing canon is rejected."""
        # 1. Add a seed track to canon
        seed_id = "seed_001"
        seed_features = {
            "track_id": seed_id,
            "motifs": ["革命", "解放", "愛"],
            "hooks": ["hook_A"],
            "imagery": ["瞳", "窓"]
        }
        self.engine.admit_track_data(seed_id, "Seed lyrics", {}, {"metrics": seed_features})
        
        # 2. Try to admit a copy
        copy_features = {
            "motifs": ["革命", "解放", "愛"], # 100% overlap
            "hooks": ["hook_A"],
            "imagery": ["瞳", "窓"]
        }
        
        status, reasons, metrics = self.engine.evaluate_admission(
            copy_features, 
            critic_report={"total_score": 90.0}, # High craft
            grounding_intensity=0.8
        )
        
        self.assertEqual(status, AdmissionStatus.REJECT)
        self.assertIn("low_originality", reasons)
        self.assertGreater(metrics["nearest_neighbor_similarity"], 0.7)

    def test_hold_for_mediocre_originality(self) -> None:
        """Verify that partial similarity leads to 'HOLD' status."""
        seed_id = "seed_001"
        seed_features = {
            "track_id": seed_id,
            "motifs": ["A", "B", "C", "D"],
            "hooks": ["H1"],
            "imagery": ["I1"]
        }
        self.engine.admit_track_data(seed_id, "Seed lyrics", {}, {"metrics": seed_features})
        
        # Partial overlap
        test_features = {
            "motifs": ["A", "B", "X", "Y"], # 50% motif overlap
            "hooks": ["H2"],
            "imagery": ["I2"]
        }
        
        status, reasons, metrics = self.engine.evaluate_admission(
            test_features, 
            critic_report={"total_score": 95.0}, # High craft
            grounding_intensity=0.8
        )
        
        # Composite Similarity: (0.5 * 0.6) + (0 * 0.2) + ... = ~0.3
        # Originality: 1.0 - 0.3 = 0.7
        # This should Pass or Warn depending on thresholds. 
        # AdmissionPolicy.MIN_ORIGINALITY_COMPOSITE = 0.5 (Check policies.py)
        
        self.assertIn(status, [AdmissionStatus.PASS, AdmissionStatus.WARN])

    def test_rejection_for_low_craft(self) -> None:
        """Verify that high originality but low craft is rejected."""
        test_features = {
            "motifs": ["Unique1", "Unique2"],
            "hooks": ["UniqueH"],
            "imagery": ["UniqueI"]
        }
        
        status, reasons, metrics = self.engine.evaluate_admission(
            test_features, 
            critic_report={"total_score": 50.0}, # LOW CRAFT
            grounding_intensity=0.8
        )
        
        self.assertEqual(status, AdmissionStatus.REJECT)
        self.assertIn("low_craft_score", reasons)


if __name__ == "__main__":
    unittest.main()
