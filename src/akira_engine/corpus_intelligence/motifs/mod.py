# src/akira_engine/corpus_intelligence/motifs/mod.py

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from .graph import build_motif_transition_graph, save_motif_graph, score_transition_novelty, sample_transition_chain
from .mining import extract_track_motif_flow


def build_motif_graph_index(
    conditioning_records: Iterable[Dict[str, Any]],
    *,
    output_path: str | Path = "data/motifs/motif_transition_graph_v1.json",
    min_support_count: int = 2,
) -> Dict[str, Any]:
    """
    Build a motif transition graph from a set of conditioning records.
    
    This is the main entry point for Week 3.
    """
    edge_candidates: List[Dict[str, Any]] = []

    for record in conditioning_records:
        # Extract motif flow per track
        edges = extract_track_motif_flow(record)
        edge_candidates.extend(edges)

    # Build graph from aggregated edges
    graph = build_motif_transition_graph(
        edge_candidates,
        min_support_count=min_support_count,
    )
    
    # Save to disk
    save_motif_graph(graph, output_path)

    return {
        "output_path": str(output_path),
        "node_count": graph.node_count,
        "edge_count": graph.edge_count,
        "version": graph.version,
    }

def compute_motif_novelty(
    graph_path: str | Path,
    chain: List[Dict[str, Any]],
) -> float:
    """Convenience function to score a chain against a saved graph."""
    from .schema import MotifGraph, MotifTransition, MotifNodeStats
    
    with open(graph_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    # Lazy reconstruction for scoring (just need transitions and stats)
    # The graph object can be reconstructed or we can use a simpler helper
    # For now, let's keep it simple
    
    # Reconstruct transitions
    transitions = {}
    for k, v in data.get("transitions", {}).items():
        transitions[k] = [
            MotifTransition(**item) for item in v
        ]
        
    graph = MotifGraph(
        version=data.get("version", "v1"),
        node_count=data.get("node_count", 0),
        edge_count=data.get("edge_count", 0),
        transitions=transitions,
        motif_stats={}, # Not strictly needed for scoring
        sampling_index=data.get("sampling_index", {})
    )
    
    return score_transition_novelty(graph, chain)
