# scripts/test_week8_canon.py

from __future__ import annotations

import unittest
import sys
import io
import json
import shutil
from pathlib import Path

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).resolve().parents[1]  # scripts/ -> AKIRA ENGINE
sys.path.insert(0, str(PROJECT_ROOT))

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from src.akira_engine.creative.canon.mod import admit_to_canon


class TestWeek8Canon(unittest.TestCase):
    def setUp(self) -> None:
        self.project_root = PROJECT_ROOT
        self.canon_dir = self.project_root / "data" / "canon_tracks"
        
        # Backup canon if it exists (for safety)
        self.temp_canon_dir = self.project_root / "data" / "canon_tracks_test_bkp"
        if self.canon_dir.exists():
            shutil.copytree(self.canon_dir, self.temp_canon_dir, dirs_exist_ok=True)

    def tearDown(self) -> None:
        # Cleanup test track
        pass # Keep for manual review if needed, or cleanup

    def test_admit_elite_track(self) -> None:
        """Verify that a high-score elite track is admitted."""
        track_id = "test_elite_001"
        lyrics = "愛してる 愛のカタチ 革命だ"
        novelty_report = {
            "composite_score": 85.0,
            "cliche_density": 0.05,
            "recombinative_novelty": 0.5
        }
        
        result = admit_to_canon(
            project_root=self.project_root,
            track_id=track_id,
            lyrics=lyrics,
            novelty_report=novelty_report
        )
        
        self.assertEqual(result["status"], "admitted")
        
        # Check if file exists
        save_path = self.canon_dir / f"{track_id}.json"
        self.assertTrue(save_path.exists())
        
        with open(save_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.assertEqual(data["track_id"], track_id)
            self.assertEqual(data["lyrics"], lyrics)

    def test_reject_low_score_track(self) -> None:
        """Verify that a low-score track is rejected."""
        track_id = "test_junk_001"
        lyrics = "平凡な歌 々しい日々"
        novelty_report = {
            "composite_score": 50.0,
            "cliche_density": 0.3, # Too high
            "recombinative_novelty": 0.1
        }
        
        result = admit_to_canon(
            project_root=self.project_root,
            track_id=track_id,
            lyrics=lyrics,
            novelty_report=novelty_report
        )
        
        self.assertEqual(result["status"], "rejected_not_elite")
        
        # Check if file exists (it should NOT)
        save_path = self.canon_dir / f"{track_id}.json"
        self.assertFalse(save_path.exists())

    def test_critic_veto(self) -> None:
        """Verify that a high novelty but low critic score is rejected."""
        track_id = "test_weird_001"
        lyrics = "意味不明な 抽象的な 叫び"
        novelty_report = {
            "composite_score": 82.0, # Pass
            "cliche_density": 0.0,   # Pass
            "recombinative_novelty": 0.8 # Pass
        }
        critic_report = {
            "overall_score": 45.0 # LOW CRITIC SCORE
        }
        
        result = admit_to_canon(
            project_root=self.project_root,
            track_id=track_id,
            lyrics=lyrics,
            novelty_report=novelty_report,
            critic_report=critic_report
        )
        
        # Should be rejected even with good novelty, because critic failed it
        self.assertEqual(result["status"], "rejected_not_elite")


if __name__ == "__main__":
    unittest.main()
