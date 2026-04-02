# src/akira_engine/corpus_intelligence/hooks/mod.py

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from .schema import HookGrammar, HookGrammarBank
from .mining import build_hook_grammar_bank, analyze_hook


def generate_hook_blueprint(
    bank_path: str | Path,
    target_mood: str = "energetic",
) -> Dict[str, Any]:
    """Generate a rhythmic/structural hook blueprint based on the grammar bank.
    
    This function will be used by the Week 5 Abstract Planner to design 
    catchy hooks without human intervention.
    """
    bank_path = Path(bank_path)
    if not bank_path.exists():
        return {"syllables": [7, 5, 7, 5], "rhyme_vowel": "a", "repetition": "none"}
        
    with open(bank_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    # Pick top pattern
    top_patterns = data.get("top_patterns", [])
    if top_patterns:
        # Use probabilistic sampling or just top 1 for now
        pattern_str = top_patterns[0].get("pattern", "7-5-7-5")
        syllables = [int(s) for s in pattern_str.split("-")]
    else:
        syllables = [7, 5, 7, 5]
        
    # Sample rhyme
    rhymes = data.get("exclamations", {}) # Using exclamations as proxy for now
    
    return {
        "syllables": syllables,
        "rhyme_vowel": "a", # default to 'a' as it's the most common open vowel
        "repetition": "anaphora" if "anaphora" in str(rhymes) else "none"
    }


def build_hook_bank_index(
    conditioning_records: List[Dict[str, Any]],
    output_path: str | Path = "data/hooks/hook_grammar_bank_v1.json"
) -> Dict[str, Any]:
    """Top-level entry point to build the hook grammar bank."""
    bank = build_hook_grammar_bank(conditioning_records, output_path=output_path)
    
    return {
        "output_path": str(output_path),
        "total_hooks": bank.total_hooks,
        "top_pattern": bank.top_syllable_patterns[0].get("pattern") if bank.top_syllable_patterns else "none"
    }
