# src/akira_engine/corpus_intelligence/hooks/schema.py

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class RhymePattern:
    """Represents a rhyme (assonance) pattern in a hook.
    
    Attributes:
        rhyme_vowel: The target vowel (a, i, u, e, o).
        line_indices: Indices of lines that rhyme.
        word_positions: Position of rhyming words (start, middle, end).
        strength: Normalized rhyme consistency (0-1).
    """
    rhyme_vowel: str = ""
    line_indices: List[int] = field(default_factory=list)
    word_positions: List[str] = field(default_factory=list)
    strength: float = 0.0


@dataclass
class HookGrammar:
    """Statistical grammar of a single hook (chorus).

    Attributes:
        track_id: Source track.
        section_name: Section name (chorus, hook, etc.).
        syllable_pattern: List of mora counts per line (e.g., [7, 5, 7, 5]).
        rhyme_schemes: List of detected rhyme patterns.
        exclamation_map: Mapping of word index to exclamation type.
        repetition_type: Type of structural repetition (none, anaphora, etc.).
        keywords: Top keywords in this hook.
    """
    track_id: str = ""
    section_name: str = ""
    syllable_pattern: List[int] = field(default_factory=list)
    rhyme_schemes: List[RhymePattern] = field(default_factory=list)
    exclamation_map: Dict[int, str] = field(default_factory=dict)
    repetition_type: str = "none"
    keywords: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "track_id": self.track_id,
            "section": self.section_name,
            "syllables": self.syllable_pattern,
            "rhyme_count": len(self.rhyme_schemes),
            "repetition": self.repetition_type,
            "keywords": self.keywords[:10]
        }


@dataclass
class HookGrammarBank:
    """Global bank of hook grammars and statistics.

    Attributes:
        version: Version of the bank.
        total_hooks: Number of hooks analyzed.
        grammars: List of all individual HookGrammar objects.
        top_syllable_patterns: Most frequent [n, n, n, n] patterns.
        common_rhymes: Frequent rhyme vowel associations.
        exclamation_stats: Frequency of "Ah", "Oh", etc.
    """
    version: str = "1.0"
    total_hooks: int = 0
    grammars: List[HookGrammar] = field(default_factory=list)
    top_syllable_patterns: List[Dict[str, Any]] = field(default_factory=list)
    common_rhymes: Dict[str, float] = field(default_factory=dict)
    exclamation_stats: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "total_hooks": self.total_hooks,
            "top_patterns": self.top_syllable_patterns[:15],
            "exclamations": self.exclamation_stats,
            "sample_grammar_count": len(self.grammars)
        }
