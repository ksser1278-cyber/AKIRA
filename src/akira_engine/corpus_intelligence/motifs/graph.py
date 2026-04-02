# src/akira_engine/corpus_intelligence/motifs/graph.py

from __future__ import annotations

import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from .schema import MotifGraph, MotifNodeStats, MotifTransition


def _edge_key(edge: Dict[str, Any]) -> Tuple[str, str, str, str, str]:
    return (
        edge["src_motif"],
        edge["dst_motif"],
        edge["transition_type"],
        edge["section_from"],
        edge["section_to"],
    )


def build_motif_transition_graph(
    edge_candidates: Iterable[Dict[str, Any]],
    *,
    min_support_count: int = 3,
    min_confidence: float = 0.3,
    max_unknown_ratio: float = 0.3,
    max_weirdness_per_node: int = 15,
) -> MotifGraph:
    grouped: Dict[Tuple[str, str, str, str, str], List[Dict[str, Any]]] = defaultdict(list)

    for edge in edge_candidates:
        grouped[_edge_key(edge)].append(edge)

    transitions: Dict[str, List[MotifTransition]] = defaultdict(list)
    motif_freq = Counter()
    incoming = Counter()
    outgoing = Counter()
    dominant_sections: Dict[str, Counter] = defaultdict(Counter)

    for (src_motif, dst_motif, transition_type, section_from, section_to), edges in grouped.items():
        support_count = len(edges)
        if support_count < min_support_count:
            continue

        avg_confidence = sum(e["confidence"] for e in edges) / support_count
        
        # Pruning: skip low-confidence edges 
        if avg_confidence < min_confidence:
            continue
            
        # Dampening: scale weight by plausibility
        plausibility_factor = min(1.0, avg_confidence / 0.7)  # Full weight at 0.7+
        weight = support_count * avg_confidence * plausibility_factor

        artists = sorted({e["artist_id"] for e in edges if e.get("artist_id")})
        modes = sorted({e["mode_id"] for e in edges if e.get("mode_id")})

        transition = MotifTransition(
            src_motif=src_motif,
            dst_motif=dst_motif,
            transition_type=transition_type,
            weight=round(weight, 4),
            confidence=round(avg_confidence, 4),
            support_count=support_count,
            section_from=section_from,
            section_to=section_to,
            context_artists=artists,
            context_modes=modes,
            context_clusters=[],
            evidence={
                "support_track_ids": sorted(
                    {e["track_id"] for e in edges if e.get("track_id")}
                )[:20]
            },
        )

        transitions[src_motif].append(transition)

        motif_freq[src_motif] += support_count
        motif_freq[dst_motif] += support_count
        outgoing[src_motif] += support_count
        incoming[dst_motif] += support_count

        dominant_sections[src_motif][section_from] += support_count
        dominant_sections[dst_motif][section_to] += support_count

    motif_stats: Dict[str, MotifNodeStats] = {}
    all_motifs = set(motif_freq.keys()) | set(incoming.keys()) | set(outgoing.keys())

    for motif in all_motifs:
        motif_stats[motif] = MotifNodeStats(
            motif=motif,
            frequency=motif_freq[motif],
            incoming_count=incoming[motif],
            outgoing_count=outgoing[motif],
            dominant_sections=dict(dominant_sections[motif]),
        )

    # Post-build pruning: unknown ratio cap and weirdness cap
    pruned_transitions: Dict[str, List[MotifTransition]] = {}
    for motif, edges in transitions.items():
        # Weirdness cap: limit edges per node
        sorted_edges = sorted(edges, key=lambda e: e.weight, reverse=True)
        capped = sorted_edges[:max_weirdness_per_node]
        
        # Unknown ratio cap
        unknown_count = sum(1 for e in capped if e.transition_type == "unknown")
        total_count = len(capped)
        if total_count > 0 and unknown_count / total_count > max_unknown_ratio:
            # Remove weakest unknowns until under cap
            non_unknown = [e for e in capped if e.transition_type != "unknown"]
            unknowns = sorted([e for e in capped if e.transition_type == "unknown"], key=lambda e: e.weight, reverse=True)
            max_unknowns = max(1, int(len(non_unknown) * max_unknown_ratio / (1 - max_unknown_ratio)))
            capped = non_unknown + unknowns[:max_unknowns]
        
        pruned_transitions[motif] = capped
        
    sampling_index = build_sampling_index(pruned_transitions)

    edge_count = sum(len(v) for v in pruned_transitions.values())

    return MotifGraph(
        version="v1",
        node_count=len(motif_stats),
        edge_count=edge_count,
        transitions=dict(pruned_transitions),
        motif_stats=motif_stats,
        sampling_index=sampling_index,
        metadata={
            "min_support_count": min_support_count,
            "min_confidence": min_confidence,
            "max_unknown_ratio": max_unknown_ratio,
            "max_weirdness_per_node": max_weirdness_per_node,
        },
    )


def build_sampling_index(
    transitions: Dict[str, List[MotifTransition]]
) -> Dict[str, Any]:
    """
    random walk 샘플링용 누적 weight 인덱스
    """
    index: Dict[str, Any] = {}

    for motif, edges in transitions.items():
        total = sum(max(edge.weight, 0.0001) for edge in edges)
        cursor = 0.0
        rows = []

        for edge in sorted(edges, key=lambda e: e.weight, reverse=True):
            prob = max(edge.weight, 0.0001) / total
            cursor += prob
            rows.append(
                {
                    "dst_motif": edge.dst_motif,
                    "transition_type": edge.transition_type,
                    "threshold": round(cursor, 8),
                }
            )

        index[motif] = rows

    return index


def sample_transition_chain(
    graph: MotifGraph,
    *,
    start_motif: str,
    max_steps: int = 4,
    rng: Optional[random.Random] = None,
) -> List[Dict[str, Any]]:
    rng = rng or random.Random()
    chain: List[Dict[str, Any]] = []
    current = start_motif

    for _ in range(max_steps):
        rows = graph.sampling_index.get(current)
        if not rows:
            break

        roll = rng.random()
        picked = None

        for row in rows:
            if roll <= row["threshold"]:
                picked = row
                break

        if picked is None:
            picked = rows[-1]

        chain.append(
            {
                "src_motif": current,
                "dst_motif": picked["dst_motif"],
                "transition_type": picked["transition_type"],
            }
        )
        current = picked["dst_motif"]

    return chain


def score_transition_novelty(
    graph: MotifGraph,
    chain: List[Dict[str, Any]],
) -> float:
    """
    novelty = rarity * plausibility * connectivity
    0.0 ~ 1.0 (높을수록 독창적)
    """
    if not chain:
        return 0.0

    edge_scores: List[float] = []

    for item in chain:
        src = item.get("src_motif")
        dst = item.get("dst_motif")
        ttype = item.get("transition_type")

        # Global stats for rarity
        all_edges_from_src = graph.transitions.get(src, [])
        if not all_edges_from_src:
            # Completely unknown transition
            edge_scores.append(0.85) # High novelty as it's unexpected
            continue

        matched = next(
            (
                e for e in all_edges_from_src
                if e.dst_motif == dst and (ttype is None or e.transition_type == ttype)
            ),
            None,
        )

        if matched is None:
            # Novel transition for this specific motif
            rarity = 0.9
            # Heuristic for plausibility: are the motifs similar in some way?
            # For now, base it on the motif's general connectivity
            plausibility = 0.4
            connectivity = min(1.0, len(all_edges_from_src) / 5.0)
        else:
            # Existing transition
            rarity = 1.0 / (1.0 + math.log1p(matched.support_count))
            plausibility = matched.confidence
            connectivity = min(1.0, len(all_edges_from_src) / 10.0)

        # Weighted combination
        score = rarity * 0.45 + plausibility * 0.35 + connectivity * 0.20
        edge_scores.append(score)

    return round(sum(edge_scores) / len(edge_scores), 4)


def save_motif_graph(graph: MotifGraph, output_path: str | Path) -> None:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(graph.to_dict(), f, ensure_ascii=False, indent=2)
