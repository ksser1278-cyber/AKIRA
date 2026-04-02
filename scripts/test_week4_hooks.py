# scripts/test_week4_hooks.py

from __future__ import annotations

import json
import tempfile
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

from src.akira_engine.corpus_intelligence.hooks.analyzer import (
    MoraCounter,
    RhymeAnalyzer,
    RepetitionMiner,
)
from src.akira_engine.corpus_intelligence.hooks.mining import (
    analyze_hook,
    build_hook_grammar_bank,
)
from src.akira_engine.corpus_intelligence.hooks.mod import (
    build_hook_bank_index,
    generate_hook_blueprint,
)


def _conditioning_record(
    *,
    track_id: str,
    sections: list[dict],
    ground_truth: list[dict],
) -> dict:
    return {
        "track_identity": {
            "track_id": track_id,
        },
        "section_analysis": sections,
        "lyric_ground_truth": {
            "sections": ground_truth,
        },
    }


def _sample_records() -> list[dict]:
    """Sample records for unit tests."""
    rec1 = _conditioning_record(
        track_id="kanaria_eye",
        sections=[
            {
                "section": "chorus_1",
                "vocabulary_focus": ["pain", "hand", "smile"],
            }
        ],
        ground_truth=[
            {
                "section_name": "Chorus 1",
                "lines": [
                    "痛いなこの手にぐさりだあ",           # Mora: 3 (i-ta-i) + 1 (na) + 2 (ko-no) + 3 (te-ni) + 3 (gu-sa-ri) + 1 (da) + 1 (a) = 14 approx
                    "30 40 狂ったようにスマイルでね", # Mora: 4 (3040) + 3 (ku-ru-tta) + 3 (yo-u-ni) + 4 (su-ma-i-ru) + 2 (de-ne) = 16 approx
                ]
            }
        ],
    )
    
    rec2 = _conditioning_record(
        track_id="pinocchiop_god_like",
        sections=[
            {
                "section": "hook",
                "vocabulary_focus": ["god", "human", "religion"],
            }
        ],
        ground_truth=[
            {
                "section_name": "Hook",
                "lines": [
                    "神っぽいな。神っぽいな。",      # Mora: 2 (ka-mi) + 4 (ppo-i-na) + 2 (ka-mi) + 4 (ppo-i-na) = 12 approx
                    "あー、ニンゲンじゃないみたいだ", # Mora: 2 (a-a) + 4 (ni-n-ge-n) + 4 (ja-na-i) + 3 (mi-ta-i) + 1 (da) = 14 approx
                ]
            }
        ],
    )
    
    return [rec1, rec2]


class TestWeek4Hooks(unittest.TestCase):
    def test_mora_counter(self) -> None:
        """Test the pure-python Mora counter."""
        self.assertEqual(MoraCounter.count_mora("あいうえお"), 5)
        self.assertEqual(MoraCounter.count_mora("きゃぴょ"), 2) # Digraphs: ki-ya, pi-yo
        self.assertEqual(MoraCounter.count_mora("っ"), 1) # Small tsu
        self.assertEqual(MoraCounter.count_mora("ー"), 1) # Prolonged
        self.assertEqual(MoraCounter.count_mora("漢字"), 4) # Est 2 per Kanji
        
    def test_rhyme_analyzer(self) -> None:
        """Test the vowel-based assonance analyzer."""
        self.assertEqual(RhymeAnalyzer.get_last_vowel("あ"), "a")
        self.assertEqual(RhymeAnalyzer.get_last_vowel("い"), "i")
        self.assertEqual(RhymeAnalyzer.get_last_vowel("う"), "u")
        self.assertEqual(RhymeAnalyzer.get_last_vowel("え"), "e")
        self.assertEqual(RhymeAnalyzer.get_last_vowel("お"), "o")
        
        # Multiline rhyme
        lines = ["痛いな", "これな"] # Both end in "na" (a)
        scheme = RhymeAnalyzer.detect_scheme(lines)
        self.assertEqual(len(scheme), 1)
        self.assertEqual(scheme[0][0], "a")
        
    def test_repetition_miner(self) -> None:
        """Test repetition detection."""
        lines = ["神っぽいな", "神っぽいな"]
        self.assertEqual(RepetitionMiner.detect_repetition(lines), "chorus_loop")
        
        lines = ["あー、ニンゲン", "あー、カミサマ"]
        self.assertEqual(RepetitionMiner.detect_repetition(lines), "anaphora")
        
    def test_analyze_hook(self) -> None:
        """Test analyze_hook logic."""
        grammar = analyze_hook("track_001", "chorus", ["あいうえお", "かきくけこ"])
        self.assertEqual(grammar.syllable_pattern, [5, 5])
        self.assertEqual(grammar.repetition_type, "none")
        
    def test_build_hook_grammar_bank(self) -> None:
        """Test building the full bank."""
        records = _sample_records()
        bank = build_hook_grammar_bank(records)
        self.assertEqual(bank.total_hooks, 2)
        self.assertGreaterEqual(len(bank.top_syllable_patterns), 1)
        
    def test_generate_hook_blueprint(self) -> None:
        """Test blueprint generation."""
        records = _sample_records()
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "hook_bank.json"
            build_hook_bank_index(records, output_path=out)
            
            blueprint = generate_hook_blueprint(out)
            self.assertIn("syllables", blueprint)
            self.assertIn("rhyme_vowel", blueprint)

if __name__ == "__main__":
    unittest.main()
