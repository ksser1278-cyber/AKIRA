# src/akira_engine/corpus_intelligence/motifs/schema.py

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Literal, Optional


TransitionType = Literal[
    "intensify",
    "distort",
    "invert",
    "release",
    "sustain",
    "unknown",
]


@dataclass(slots=True)
class SectionMotifSnapshot:
    section_name: str
    motifs: List[str]
    dominant_motifs: List[str]
    emotion_tags: List[str] = field(default_factory=list)
    source_track_id: Optional[str] = None
    artist_id: Optional[str] = None
    mode_id: Optional[str] = None


@dataclass(slots=True)
class MotifTransition:
    src_motif: str
    dst_motif: str
    transition_type: TransitionType
    weight: float
    confidence: float
    support_count: int

    section_from: str
    section_to: str

    context_artists: List[str] = field(default_factory=list)
    context_modes: List[str] = field(default_factory=list)
    context_clusters: List[str] = field(default_factory=list)

    evidence: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class MotifNodeStats:
    motif: str
    frequency: int
    incoming_count: int
    outgoing_count: int
    dominant_sections: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class MotifGraph:
    version: str
    node_count: int
    edge_count: int

    transitions: Dict[str, List[MotifTransition]]
    motif_stats: Dict[str, MotifNodeStats]

    sampling_index: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "node_count": self.node_count,
            "edge_count": self.edge_count,
            "transitions": {
                k: [edge.to_dict() for edge in v]
                for k, v in self.transitions.items()
            },
            "motif_stats": {
                k: v.to_dict() for k, v in self.motif_stats.items()
            },
            "sampling_index": self.sampling_index,
            "metadata": self.metadata,
        }
