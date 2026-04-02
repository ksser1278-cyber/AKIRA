# src/akira_engine/corpus_intelligence/hooks/mining.py

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from .schema import HookGrammar, HookGrammarBank, RhymePattern
from .analyzer import MoraCounter, RhymeAnalyzer, RepetitionMiner


def analyze_hook(
    track_id: str,
    section_name: str,
    lines: List[str],
    keywords: List[str] = None
) -> HookGrammar:
    """Analyze a single hook's grammar properties."""
    
    # 1. Syllable pattern
    syllables = [MoraCounter.count_mora(line) for line in lines]
    
    # 2. Rhyme schemes
    rhyme_patterns = []
    schemes = RhymeAnalyzer.detect_scheme(lines)
    for vowel, indices in schemes:
        rhyme_patterns.append(RhymePattern(
            rhyme_vowel=vowel,
            line_indices=indices,
            strength=len(indices) / len(lines) if lines else 0.0
        ))
        
    # 3. Repetition
    repetition = RepetitionMiner.detect_repetition(lines)
    
    return HookGrammar(
        track_id=track_id,
        section_name=section_name,
        syllable_pattern=syllables,
        rhyme_schemes=rhyme_patterns,
        repetition_type=repetition,
        keywords=keywords or []
    )


def build_hook_grammar_bank(
    conditioning_records: List[Dict[str, Any]],
    output_path: Optional[str | Path] = None
) -> HookGrammarBank:
    """Scan corpus and build the global hook grammar bank."""
    
    grammars = []
    
    for record in conditioning_records:
        track_id = record.get("track_identity", {}).get("track_id", "unknown")
        
        # 1. Look for chorus/hook in section_analysis
        sections = record.get("section_analysis", [])
        for sec in sections:
            name = sec.get("section", sec.get("section_name", "")).lower()
            
            # Identify hooks/choruses/sabi
            if any(term in name for term in ["chorus", "hook", "sabi", "사비"]):
                # Get lines from ground truth
                lines = []
                # Try to map lines from ground truth sections
                lgt = record.get("lyric_ground_truth", {}).get("sections", [])
                
                # Normalize name for matching (replace underscore with space, etc.)
                norm_name = name.replace("_", " ").strip()
                
                for gs in lgt:
                    gs_name = gs.get("section_name", "").lower().replace("_", " ").strip()
                    if norm_name in gs_name or gs_name in norm_name:
                        lines = gs.get("lines", [])
                        break
                
                # Fallback: if no ground truth, skip or estimate
                if not lines:
                    continue
                
                # Analyze grammar
                grammar = analyze_hook(
                    track_id=track_id,
                    section_name=name,
                    lines=lines,
                    keywords=sec.get("vocabulary_focus", [])
                )
                grammars.append(grammar)

    # Calculate statistics
    total = len(grammars)
    
    # top_syllable_patterns
    patterns = Counter()
    for g in grammars:
        # Normalize pattern to string like "7-7-7-5"
        p_str = "-".join(map(str, g.syllable_pattern))
        if p_str:
            patterns[p_str] += 1
            
    top_patterns = [
        {"pattern": p, "count": count, "ratio": round(count / (total or 1), 4)}
        for p, count in patterns.most_common(20)
    ]
    
    # common_rhymes
    rhymes = Counter()
    for g in grammars:
        for r in g.rhyme_schemes:
            rhymes[r.rhyme_vowel] += 1
            
    rhyme_stats = {
        v: round(count / (total or 1), 4)
        for v, count in rhymes.items()
    }
    
    # repetition
    repetition = Counter()
    for g in grammars:
        repetition[g.repetition_type] += 1

    bank = HookGrammarBank(
        version="1.0",
        total_hooks=total,
        grammars=grammars,
        top_syllable_patterns=top_patterns,
        common_rhymes=rhyme_stats,
        exclamation_stats=dict(repetition) # using repetition as exclamation proxy for now
    )
    
    # Save if path provided
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(bank.to_dict(), f, ensure_ascii=False, indent=2)
            
    return bank
