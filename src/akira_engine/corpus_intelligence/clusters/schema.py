"""Style Clusters — Data Schemas.

Defines data structures for expression-axis clustering of the corpus.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class StyleCluster:
    """Represents a single style cluster discovered in the corpus.

    Attributes:
        cluster_id: Unique identifier (e.g., "cluster_03").
        label: Human-readable auto-generated label (e.g., "dark_somatic_intense").
        size: Number of tracks in this cluster.
        dominant_atoms: Most frequent atoms across cluster members.
        dominant_categories: Category distribution (body/scene/sound/motif ratios).
        dominant_structure_patterns: Common section structures.
        emotional_profile: Dominant emotional characteristics.
        centroid: Feature vector centroid for distance calculations.
        member_track_ids: List of track_ids belonging to this cluster.
    """
    cluster_id: str = ""
    label: str = ""
    size: int = 0
    dominant_atoms: list[str] = field(default_factory=list)
    dominant_categories: dict[str, float] = field(default_factory=dict)
    dominant_structure_patterns: list[str] = field(default_factory=list)
    emotional_profile: list[str] = field(default_factory=list)
    centroid: list[float] = field(default_factory=list)
    member_track_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "cluster_id": self.cluster_id,
            "label": self.label,
            "size": self.size,
            "dominant_atoms": self.dominant_atoms[:15],
            "dominant_categories": self.dominant_categories,
            "emotional_profile": self.emotional_profile,
            "member_track_ids": self.member_track_ids,
        }


@dataclass
class ClusterAssignment:
    """Cluster membership assignment for a single track or candidate.

    Attributes:
        track_id: The track being assigned.
        primary_cluster: Closest cluster.
        secondary_cluster: Second closest (for cross-pollination analysis).
        distances: Distance to each cluster centroid.
        membership_scores: Normalized similarity to each cluster (0-1).
    """
    track_id: str = ""
    primary_cluster: str = ""
    secondary_cluster: str = ""
    distances: dict[str, float] = field(default_factory=dict)
    membership_scores: dict[str, float] = field(default_factory=dict)

    def cluster_ids(self) -> list[str]:
        """Return cluster IDs sorted by membership score (desc)."""
        return sorted(
            self.membership_scores.keys(),
            key=lambda k: self.membership_scores.get(k, 0.0),
            reverse=True,
        )


@dataclass
class ClusterMap:
    """Complete cluster map of the corpus.

    Attributes:
        version: Schema version.
        k: Number of clusters.
        clusters: List of discovered clusters.
        assignments: Per-track cluster assignments.
        atom_cluster_map: Mapping of atom -> primary cluster_id.
    """
    version: str = "1.0"
    k: int = 0
    clusters: list[StyleCluster] = field(default_factory=list)
    assignments: list[ClusterAssignment] = field(default_factory=list)
    atom_cluster_map: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "k": self.k,
            "clusters": [c.to_dict() for c in self.clusters],
            "assignments": [
                {
                    "track_id": a.track_id,
                    "primary": a.primary_cluster,
                    "secondary": a.secondary_cluster,
                    "scores": a.membership_scores,
                }
                for a in self.assignments
            ],
            "atom_cluster_map_size": len(self.atom_cluster_map),
        }
