# src/akira_engine/creative/planner/schema.py

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class CreativeSection:
    """Represents a planned section of a song.
    
    Attributes:
        section_name: Name of the section (e.g., "verse_1", "chorus").
        function: Narrative or structural function (e.g., "setup", "release", "twist").
        primary_motif: The main semantic theme for this section.
        secondary_motifs: Supporting themes.
        imagery_anchors: Specific sensory atoms to ground the section.
        syllable_target: Rhythm pattern (e.g., "8-8-7-5").
        rhyme_vowel: Target assonance (e.g., "a").
        abstraction_ceiling: Maximum allowed abstraction ratio (from features).
    """
    section_name: str
    function: str = "narrative"
    primary_motif: str = ""
    secondary_motifs: List[str] = field(default_factory=list)
    imagery_anchors: List[str] = field(default_factory=list)
    syllable_target: List[int] = field(default_factory=list)
    rhyme_vowel: Optional[str] = None
    abstraction_ceiling: float = 0.2
    grounding_intensity: float = 0.5
    narrative_intent: str = "setup"
    token_density_target: str = "airy"


@dataclass
class AbstractBlueprint:
    """Complete high-level creative plan for a song.
    
    Attributes:
        track_id: Unique identifier for this generation.
        target_artist_id: Artist style to emulate (if any).
        target_mode_id: Production mode (e.g., "dark_cute_breakdown").
        primary_cluster: Style cluster ID the plan is based on.
        thematic_chain: The sequence of motifs from the transition graph.
        sections: List of CreativeSection objects.
        creativity_index: 0-1 score representing how "novel" the plan is.
        metadata: Additional generation metadata (timestamps, etc.).
    """
    track_id: str
    target_artist_id: str = ""
    target_mode_id: str = "default"
    primary_cluster: str = ""
    thematic_chain: List[Dict[str, Any]] = field(default_factory=list)
    sections: List[CreativeSection] = field(default_factory=list)
    creativity_index: float = 0.5
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "track_id": self.track_id,
            "artist": self.target_artist_id,
            "mode": self.target_mode_id,
            "cluster": self.primary_cluster,
            "creativity": self.creativity_index,
            "chain": self.thematic_chain,
            "sections": [
                {
                    "name": s.section_name,
                    "function": s.function,
                    "motifs": [s.primary_motif] + s.secondary_motifs,
                    "imagery": s.imagery_anchors,
                    "syllables": "-".join(map(str, s.syllable_target)) if s.syllable_target else None
                }
                for s in self.sections
            ]
        }
