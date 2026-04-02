"""Novelty Index — Data Schemas.

Defines the core data structures for originality profiling of generated lyrics.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class NeighborHit:
    """Represents a single nearest-neighbor match against the corpus."""
    track_id: str = ""
    artist_id: str = ""
    similarity: float = 0.0
    atom_jaccard: float = 0.0


@dataclass
class NoveltyProfile:
    """Complete originality profile for a single generated candidate.

    Attributes:
        track_id: Candidate identifier.
        nearest_external_track: Top match from external corpus (reference data).
        nearest_internal_track: Top match from engine's own internal canon.
        external_similarity: 0.0 (unique) — 1.0 (identical) text-level similarity.
        internal_similarity: Same metric against internal canon.
        artist_imitation_risk: 0.0 (no risk) — 1.0 (direct copy) imitation score.
        cliche_density: Proportion of lines containing high-frequency cliché patterns.
        recombinative_novelty: Score for cross-cluster combination (higher = more novel).
        top_k_external: List of top-k nearest neighbors from external corpus.
        top_k_internal: List of top-k nearest neighbors from internal canon.
        status: Processing state.
    """
    track_id: str = ""
    nearest_external_track: NeighborHit = field(default_factory=NeighborHit)
    nearest_internal_track: NeighborHit = field(default_factory=NeighborHit)
    external_similarity: float = 0.0
    internal_similarity: float = 0.0
    artist_imitation_risk: float = 0.0
    cliche_density: float = 0.0
    recombinative_novelty: float = 0.0
    top_k_external: list[NeighborHit] = field(default_factory=list)
    top_k_internal: list[NeighborHit] = field(default_factory=list)
    status: str = "pending"

    def composite_score(self) -> float:
        """Weighted composite: lower external/internal sim + lower imitation + lower cliché + higher recomb = better.

        Returns 0.0 (poor originality) — 100.0 (maximum originality).
        """
        ext_penalty = self.external_similarity * 30      # 30% weight
        int_penalty = self.internal_similarity * 15       # 15% weight
        imit_penalty = self.artist_imitation_risk * 25    # 25% weight
        cliche_penalty = self.cliche_density * 15         # 15% weight
        recomb_bonus = self.recombinative_novelty * 15    # 15% weight
        raw = 100.0 - ext_penalty - int_penalty - imit_penalty - cliche_penalty + recomb_bonus
        return round(max(0.0, min(100.0, raw)), 2)

    def to_dict(self) -> dict[str, Any]:
        return {
            "track_id": self.track_id,
            "external_similarity": self.external_similarity,
            "internal_similarity": self.internal_similarity,
            "artist_imitation_risk": self.artist_imitation_risk,
            "cliche_density": self.cliche_density,
            "recombinative_novelty": self.recombinative_novelty,
            "composite_score": self.composite_score(),
            "nearest_external": {
                "track_id": self.nearest_external_track.track_id,
                "artist_id": self.nearest_external_track.artist_id,
                "similarity": self.nearest_external_track.similarity,
            },
            "nearest_internal": {
                "track_id": self.nearest_internal_track.track_id,
                "similarity": self.nearest_internal_track.similarity,
            },
            "top_k_external_count": len(self.top_k_external),
            "top_k_internal_count": len(self.top_k_internal),
            "status": self.status,
        }
